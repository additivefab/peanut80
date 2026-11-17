"""ADF50 event/state reference model. Generates intentions only; NO GPIO/laser control.
Adapted for ADF50 V0.6 from the reference model of the third-party package ZL80_ADF50_V05_20261117 (control/adf_controller.py).
ECR-G3-01 was approved on 2026-11-17, so dual_follower defaults to True; the job still needs metrology_qualified from the system.
V0.6 changes: exit_s default is this design's eject-nip path position (271.7 mm); optional dual_follower mode
(ECR-G3-01, encoder on the exit pressure roller) lets the scan start before the main nip grips and removes the
47 mm head/tail ROI limits; entry rollers keep driving while the head is shorter than 42+margin.
This model has not been deployed to B10/PLC. Bench/HIL and safety validation are mandatory.
"""
from dataclasses import dataclass,asdict
from enum import Enum
import math

class State(str,Enum):
    IDLE='IDLE';FEED='FEED';PARK='PARK';TRANSFER_IN='TRANSFER_IN';SCAN='SCAN'
    AFTER_SCAN='AFTER_SCAN';TRANSFER_OUT='TRANSFER_OUT';EJECT='EJECT';STACK='STACK';DONE='DONE';FAULT='FAULT'

@dataclass
class Inputs:
    t_s:float=0
    leading_s_mm:float=-400
    safe_loop:bool=True
    module_locked:bool=True
    us_recipe_qualified:bool=False
    sensor_health:bool=True
    double_detected:bool=False
    entire_sheet_checked:bool=False
    master_grip:bool=False
    measure_valid:bool=False
    exit_grip:bool=False
    exit_speed_matched:bool=False
    master_tail_clear:bool=False
    scan_end_ack:bool=False
    raw_integrity_ok:bool=False
    output_tail_clear:bool=False
    return_gate_closed:bool=False
    stack_transfer_done:bool=False
    stack_space:bool=True
    metrology_qualified:bool=False
    tension_ok:bool=True
    follower_agree:bool=True
    encoder_ok:bool=True

class ADFController:
    def __init__(self,exit_s=271.7010721276371,grip_margin=5,heartbeat_timeout_s=.25):
        self.exit_s=exit_s;self.margin=grip_margin;self.timeout=heartbeat_timeout_s
        self.state=State.IDLE;self.events=[];self.invalid=False;self.reason='';self.last_t=None
        self.total_length=0;self.leader=0;self.roi=(0,0);self.valid_roi=False;self.scan_was_requested=False
        self.output_count=0;self.job_id='';self.entire_checked=False;self.last_leading=None
    def begin(self,job_id,length_mm=300,roi=(0,300),leader_mm=0,trailer_mm=0,carrier_qualified=False,transport_only=False,dual_follower=True):
        if self.state not in (State.IDLE,State.DONE):raise RuntimeError('job still active or fault must be manually cleared')
        if not job_id:raise ValueError('job ID required')
        if not all(math.isfinite(v) for v in [length_mm,*roi,leader_mm,trailer_mm]):raise ValueError('finite geometry required')
        if not 260<=length_mm<=300:raise ValueError('baseline length range 260..300; carrier extensions separate')
        if min(leader_mm,trailer_mm)<0:raise ValueError('extensions cannot be negative')
        if (leader_mm or trailer_mm) and not carrier_qualified:raise ValueError('carrier and ultrasound recipe not qualified')
        lo=max(0,42+self.margin-leader_mm);hi=min(length_mm,length_mm-(42+self.margin-trailer_mm))
        if dual_follower:lo,hi=0,length_mm
        self.dual=dual_follower
        if not transport_only and not (0<=roi[0]<roi[1]<=length_mm and roi[0]>=lo and roi[1]<=hi):
            raise ValueError(f'requested ROI outside measured transport window [{lo},{hi}]; no silent cropping')
        self.total_length=length_mm+leader_mm+trailer_mm;self.leader=leader_mm;self.roi=tuple(roi)
        self.transport_only=transport_only;self.job_id=job_id;self.invalid=False;self.reason='';self.last_t=None
        self.last_leading=None;self.entire_checked=False;self.scan_was_requested=False;self.state=State.FEED
    def fail(self,reason):
        self.invalid=True;self.reason=reason;self.state=State.FAULT
    def reset_fault(self,path_empty,manual_ack):
        if not(path_empty and manual_ack):raise ValueError('manual acknowledgement and empty path required')
        self.state=State.IDLE;self.last_t=None
    def step(self,i:Inputs):
        if not math.isfinite(i.t_s) or not math.isfinite(i.leading_s_mm):self.fail('NONFINITE_POSITION_OR_TIME')
        if self.last_t is not None and (i.t_s<=self.last_t or i.t_s-self.last_t>self.timeout):self.fail('TIME_OR_HEARTBEAT')
        if self.last_leading is not None and i.leading_s_mm<self.last_leading-0.2:self.fail('UNCOMMANDED_REVERSE')
        self.last_t=i.t_s;self.last_leading=i.leading_s_mm
        if not(i.safe_loop and i.module_locked and i.sensor_health):self.fail('INTERLOCK_OR_SENSOR')
        if i.double_detected:self.fail('DOUBLE_SHEET_LATCHED')
        if not(i.tension_ok and i.encoder_ok):self.fail('TENSION_OR_ENCODER')
        if not i.stack_space and self.state not in [State.IDLE,State.DONE]:self.fail('OUTPUT_FULL')
        if not i.us_recipe_qualified and self.state not in [State.IDLE,State.DONE]:self.fail('US_RECIPE_UNQUALIFIED')
        self.entire_checked=self.entire_checked or i.entire_sheet_checked
        head=i.leading_s_mm;tail=head-self.total_length
        if self.state==State.FEED and head>=-35:self.state=State.PARK
        elif self.state==State.PARK:self.state=State.TRANSFER_IN
        elif self.state==State.TRANSFER_IN:
            ready_main=head>=42+self.margin and i.master_grip
            ok=i.measure_valid and i.metrology_qualified and head>=self.leader+self.roi[0]
            if self.transport_only:
                if ready_main:self.state=State.AFTER_SCAN
            elif self.dual:
                if ok and (ready_main or head<42+self.margin):self.state=State.SCAN
            elif ready_main and ok:self.state=State.SCAN
        elif self.state==State.SCAN:
            need_main=not(self.dual and head<42+self.margin)
            if self.dual and 42+self.margin<=head<=self.total_length-(42+self.margin) and not i.follower_agree:self.fail('FOLLOWER_MISMATCH')
            if not((i.master_grip or not need_main) and i.measure_valid and i.metrology_qualified):self.fail('METROLOGY_LOST')
            elif head>=self.leader+self.roi[1]:self.state=State.AFTER_SCAN
        elif self.state==State.AFTER_SCAN:
            if head>=self.exit_s+self.margin and tail>=12:self.state=State.TRANSFER_OUT
        elif self.state==State.TRANSFER_OUT:
            # Overlap must be established before the primary nip releases the tail.
            if tail>42 and not(i.exit_grip and i.exit_speed_matched):self.fail('MISSED_OUTPUT_HANDOFF')
            elif tail>=45 and i.master_tail_clear and i.exit_grip and i.exit_speed_matched and (i.scan_end_ack or self.transport_only):self.state=State.EJECT
        elif self.state==State.EJECT:
            if i.output_tail_clear:self.state=State.STACK
        elif self.state==State.STACK:
            if i.return_gate_closed and i.stack_transfer_done:
                if not self.transport_only and not(self.entire_checked and i.scan_end_ack and i.raw_integrity_ok):self.fail('INCOMPLETE_QUALITY_EVIDENCE')
                else:self.output_count+=1;self.state=State.DONE
        hold=self.state in (State.FEED,State.PARK,State.TRANSFER_IN) or (self.state==State.SCAN and head<42+self.margin)
        out={'state':self.state.value,'job_id':self.job_id,'laser_request':False,
             'capture_request':self.state==State.SCAN and not self.invalid,
             'entry_drive_follow':hold,
             'entry_nip_open':(not hold) and self.state in (State.SCAN,State.AFTER_SCAN,State.TRANSFER_OUT,State.EJECT,State.STACK,State.DONE),
             'exit_drive_follow':self.state==State.TRANSFER_OUT,
             'exit_nip_close':self.state in (State.TRANSFER_OUT,State.EJECT),
             'eject_fast_allowed':self.state==State.EJECT,
             'hold_provisional_raw':self.state not in [State.DONE,State.IDLE] and not self.invalid,
             'quality':'INVALID' if self.invalid else ('TRANSPORT_ONLY' if getattr(self,'transport_only',False) else 'PROVISIONAL'),
             'fault':self.reason,'sheet_reverse_allowed':False,'implementation':'REFERENCE_MODEL_NO_HARDWARE_IO'}
        if self.state==State.DONE and not self.transport_only:out['quality']='ELIGIBLE_FOR_HOST_REVIEW'
        if self.state==State.FAULT:
            for k in ['capture_request','entry_drive_follow','exit_drive_follow','exit_nip_close','eject_fast_allowed']:out[k]=False
        self.events.append({'synthetic':True,'time_s':i.t_s,'input':asdict(i),'intent':out})
        return out
