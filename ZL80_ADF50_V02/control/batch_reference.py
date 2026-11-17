"""Reference batch bookkeeping and guards, NOT deployable motor/laser safety firmware.
No hardware access. Sensors, filtering, watchdogs, braking and fault isolation are external.
"""
from dataclasses import dataclass
from enum import Enum

class State(str, Enum):
    IDLE='IDLE'; NEUTRALIZE='NEUTRALIZE'; SEPARATE='SEPARATE'
    QUALIFY='QUALIFY'; PARK='PARK'; HANDOFF='HANDOFF'; SCAN='SCAN'
    EJECT='EJECT'; HOLD='HOLD'; DONE='DONE'

@dataclass(frozen=True)
class HandoffEvidence:
    full_sheet_single: bool
    input_scan_nip_engaged: bool
    pickup_released: bool
    retard_released: bool
    all_buffer_nips_released: bool
    ionizer_disabled: bool
    air_off: bool
    analog_settled: bool
    hardware_permit: bool
    output_not_full: bool
    skew_ok: bool
    position_ok: bool
    def valid(self): return all(vars(self).values())

class Batch:
    def __init__(self,target=50,max_retries=2):
        if target<1: raise ValueError('target must be positive')
        self.target=target;self.max_retries=max_retries;self.state=State.IDLE
        self.completed=0;self.attempt=0;self.job_id=None;self.records=[]
        self.retries=0;self.full_sheet=False;self.file_committed=False;self.reason=''
    def require(self,s):
        if self.state!=s: raise RuntimeError(f'Expected {s.value}, got {self.state.value}')
    def request(self,cover_closed=True,exit_space=True,stock=True):
        self.require(State.IDLE)
        if not(cover_closed and exit_space and stock):return self.hold('Precondition or early-empty failure')
        if self.completed>=self.target:return self.hold('Unexpected request after target')
        self.job_id=f'F{self.completed+1:03d}';self.attempt+=1;self.retries=0
        self.full_sheet=False;self.file_committed=False;self.state=State.NEUTRALIZE
    def neutralized(self,ok=True):
        self.require(State.NEUTRALIZE)
        if not ok:return self.hold('Ionizer / airflow / qualified recipe failed')
        self.state=State.SEPARATE
    def lead_arrived(self):self.require(State.SEPARATE);self.state=State.QUALIFY
    def qualify(self,whole_length_seen,all_single,length_ok,diagnostics_ok):
        self.require(State.QUALIFY)
        if not whole_length_seen:return False
        if not(all_single and length_ok and diagnostics_ok):return self.hold('Full-sheet verification failed; count not advanced')
        self.full_sheet=True;self.state=State.PARK;return True
    def park(self,position_ok=True,skew_ok=True):
        self.require(State.PARK)
        if not(position_ok and skew_ok):return self.hold('Parking / skew failure')
        self.state=State.HANDOFF
    def handoff(self,evidence):
        self.require(State.HANDOFF)
        if not(self.full_sheet and evidence.valid()):return self.hold('Not mechanically isolated or not safe/stable')
        self.state=State.SCAN
    def scan_end(self,raw_valid,file_durable):
        self.require(State.SCAN)
        if not(raw_valid and file_durable):return self.hold('Raw invalid or file not durably stored')
        self.file_committed=True;self.state=State.EJECT
    def receive(self,tail_clear,receipt_confirmed,stock_empty=False):
        self.require(State.EJECT)
        if not(tail_clear and receipt_confirmed and self.file_committed):return self.hold('Physical delivery unconfirmed')
        self.records.append({'job_id':self.job_id,'attempt':self.attempt,'retries':self.retries,'valid_file':True,'delivered':True})
        self.completed+=1
        if self.completed==self.target:
            if not stock_empty:return self.hold('Target reached but remaining stock/count unresolved')
            self.state=State.DONE
        else:self.state=State.IDLE
    def retry_before_scan(self,return_path_safe,count_and_order_preserved):
        if self.state not in (State.SEPARATE,State.QUALIFY,State.PARK):raise RuntimeError('Reverse forbidden after handoff/scan')
        if not(return_path_safe and count_and_order_preserved) or self.retries>=self.max_retries:return self.hold('Retry unsafe / exhausted')
        self.retries+=1;self.attempt+=1;self.full_sheet=False;self.state=State.NEUTRALIZE
    def hold(self,reason):
        self.reason=reason;self.state=State.HOLD;return False
    def emergency(self,reason='Hardware fault'):self.hold(reason)
    def scan_permission(self,hardware_permit):
        # A software permission for tests only. Physical laser enable must be independently gated.
        return self.state==State.SCAN and self.full_sheet and bool(hardware_permit)
