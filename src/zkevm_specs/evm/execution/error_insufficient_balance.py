from ...util import FQ
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag, AccountFieldTag
from ..execution_state import ExecutionState
from ..opcode import Opcode


def insufficient_balance(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    # current executing op code must be Call, CallCode， Create & Create2
    instruction.constrain_in(
        opcode, [FQ(Opcode.CALL), FQ(Opcode.CALLCODE), FQ(Opcode.CREATE), FQ(Opcode.CREATE2)]
    )
    # TODO: for create/create2 have different stack from Call, will handle it in the future
    # below we only handle call case
    instruction.stack_pop()
    instruction.stack_pop()
    value_rlc = instruction.stack_pop()
    value = instruction.rlc_to_fq(value_rlc, 31)
    caller_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)
    caller_balance_rlc = instruction.account_read(caller_address, AccountFieldTag.Balance)
    caller_balance = instruction.rlc_to_fq(caller_balance_rlc, 31)
    is_insufficient, _ = instruction.compare(caller_balance, value, 31)

    instruction.constrain_equal(is_insufficient, FQ(1))

    # current call must be failed.
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess)
    instruction.constrain_equal(is_success, FQ(0))

    # Go to EndTx only when is_root
    is_to_end_tx = instruction.is_equal(instruction.next.execution_state, ExecutionState.EndTx)
    instruction.constrain_equal(FQ(instruction.curr.is_root), is_to_end_tx)

    if instruction.curr.is_root:
        # Do step state transition
        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(6 + instruction.curr.reversible_write_counter),
            call_id=Transition.same(),
        )
    else:
        # when it is internal call, need to restore caller's state as finishing this call.
        # Restore caller state to next StepState
        instruction.step_state_transition_to_restored_context(
            rw_counter_delta=6 + instruction.curr.reversible_write_counter.n,
            return_data_offset=FQ(0),
            return_data_length=FQ(0),
            gas_left=instruction.curr.gas_left,
        )
