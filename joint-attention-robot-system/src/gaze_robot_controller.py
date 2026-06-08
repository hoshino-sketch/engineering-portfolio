#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import moveit_commander
import math
import socket
import time
import sys
import actionlib
import csv
import select
import tkinter as tk
import threading
from control_msgs.msg import FollowJointTrajectoryAction, FollowJointTrajectoryGoal
from trajectory_msgs.msg import JointTrajectoryPoint

# --- 判定・変換用定数 ---

def get_gaze_target(yaw, pitch):
    if yaw > 15 and pitch < -15: return "Left"
    elif -15 < yaw < 15 and pitch < -15: return "Center"
    elif -15 < yaw < 15 and pitch > -15: return "Robot"
    elif yaw < -15 and pitch < -15: return "Right"
    else: return "Other"

def check_is_looking_correct(mode, y, p):
    if not mode: return False
    if "Rev" in mode["name"] or mode["name"] in ["4","5","6"]:
        return mode["shake_check"](y, p)
    elif mode["type"] == "DYNAMIC":
        return mode["nod_check"](y, p)
    elif mode["type"] == "NONE":
        return mode["check"](y, p)
    return False

# --- 視覚インジケータ ---
class VisualIndicator:
    def __init__(self):
        self.show_flag = False
        self.running = True
        self.root = None
        self.label_var = None

    def run(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.geometry("300x80+10+10")
        self.root.attributes("-topmost", True)
        self.root.configure(bg='black')
        self.label_var = tk.StringVar()
        self.label_var.set("WAITING")
        label = tk.Label(self.root, textvariable=self.label_var, 
                         fg='white', bg='red', 
                         font=("Helvetica", 18, "bold"),
                         padx=10, pady=10)
        label.pack(expand=True, fill='both')

        def check_status():
            if self.show_flag:
                self.root.deiconify()
                label_text = globals().get('current_phase', 'WAITING')
                if globals().get('user_reset_requested', False):
                    label_text = "RESETTING"
                elif globals().get('active_mode') and globals().get('active_mode')['type'] == "NONE" and label_text not in ["BASELINE", "MOVING"]:
                    label_text = "POINTING"
                self.label_var.set(label_text)
            else:
                self.root.withdraw()
            if self.running:
                self.root.after(100, check_status)
            else:
                self.root.destroy()
        self.root.after(100, check_status)
        self.root.mainloop()

    def show(self): self.show_flag = True
    def hide(self): self.show_flag = False
    def stop(self): self.running = False

class NeckPitch(object):
    def __init__(self, action_name="/sciurus17/controller3/neck_controller/follow_joint_trajectory", wait=5.0):
        self._client = actionlib.SimpleActionClient(action_name, FollowJointTrajectoryAction)
        self._client.wait_for_server(rospy.Duration(wait))
    def set_angle(self, yaw_angle_rad, pitch_angle_rad, time_s=1.0, wait=True):
        goal = FollowJointTrajectoryGoal()
        goal.trajectory.joint_names = ["neck_yaw_joint", "neck_pitch_joint"]
        p = JointTrajectoryPoint()
        p.positions = [yaw_angle_rad, pitch_angle_rad]
        p.time_from_start = rospy.Duration(time_s)
        goal.trajectory.points.append(p)
        self._client.send_goal(goal)
        if wait: self._client.wait_for_result(rospy.Duration(time_s + 1.0))

#メイン処理
def main():
    moveit_commander.roscpp_initialize(sys.argv)
    rospy.init_node("gaze_experiment_system_final", anonymous=True)
    arm_neck_group = moveit_commander.MoveGroupCommander("two_arm_waist_group")
    arm_neck_group.set_max_velocity_scaling_factor(1.0)
    arm_neck_group.set_max_acceleration_scaling_factor(0.5)
    neck = NeckPitch()
    indicator = VisualIndicator()
    threading.Thread(target=indicator.run, daemon=True).start()

    #定数・パラメータ
    JA_WAIT_DEFAULT = 0.3
    JA_WAIT_SHORT = 0.3
    JA_TIMEOUT_DURATION = 0.3 
    BASELINE_DURATION = 1.0
    MOVING_DURATION = 2.0 

    #ロボットポーズ定義
    pose_L = {"neck_yaw_joint": math.radians(50.0), "neck_pitch_joint": math.radians(-40.0), "waist_yaw_joint": 0.0, "l_arm_joint1": -0.087, "l_arm_joint2": 1.108, "l_arm_joint3": 0.397, "l_arm_joint4": -1.979, "l_arm_joint5": 0.259, "l_arm_joint6": 1.344, "l_arm_joint7": -1.023}
    pose_C = {"neck_yaw_joint": math.radians(0.0), "neck_pitch_joint": math.radians(-40.0), "waist_yaw_joint": 0.0, "l_arm_joint1": -0.390, "l_arm_joint2": 1.408, "l_arm_joint3": 0.937, "l_arm_joint4": -1.789, "l_arm_joint5": 0.324, "l_arm_joint6": 1.427, "l_arm_joint7": -0.884}
    pose_R = {"neck_yaw_joint": math.radians(-50.0), "neck_pitch_joint": math.radians(-40.0), "waist_yaw_joint": 0.0, "r_arm_joint1": 0.087, "r_arm_joint2": -1.108, "r_arm_joint3": -0.397, "r_arm_joint4": 1.979, "r_arm_joint5": -0.259, "r_arm_joint6": -1.344, "r_arm_joint7": 1.023}
    pose_LC_mid = {"neck_yaw_joint": math.radians(20.0), "neck_pitch_joint": math.radians(-40.0), "waist_yaw_joint": 0.0, "l_arm_joint1": -0.055, "l_arm_joint2": 1.568, "l_arm_joint3": 0.104, "l_arm_joint4": -2.103, "l_arm_joint5": 0.044, "l_arm_joint6": 1.598, "l_arm_joint7": -0.086}
    pose_RC_mid = {"neck_yaw_joint": math.radians(-20.0), "neck_pitch_joint": math.radians(-40.0), "waist_yaw_joint": 0.0, "r_arm_joint1": 0.055, "r_arm_joint2": -1.568, "r_arm_joint3": -0.104, "r_arm_joint4": 2.103, "r_arm_joint5": -0.044, "r_arm_joint6": -1.598, "r_arm_joint7": 0.086}

    MODES = {
        "1": {"name": "L_Dyn", "type": "DYNAMIC", "pose": pose_L, "ja_dur": JA_WAIT_DEFAULT, "interval": 1.7, "nod_check": lambda y, p: y > 15.0 and p < -15.0, "shake_check": lambda y, p: y <= 15.0 and p < -15.0},
        "2": {"name": "C_Dyn", "type": "DYNAMIC", "pose": pose_C, "ja_dur": JA_WAIT_DEFAULT, "interval": 1.7, "nod_check": lambda y, p: -15.0 < y < 15.0 and p < -15.0, "shake_check": lambda y, p: (y >= 15.0 or y <= -15.0) and p < -15.0},
        "3": {"name": "R_Dyn", "type": "DYNAMIC", "pose": pose_R, "ja_dur": JA_WAIT_DEFAULT, "interval": 1.7, "nod_check": lambda y, p: y < -15.0 and p < -15.0, "shake_check": lambda y, p: y >= -15.0 and p < -15.0},
        "4": {"name": "L_Rev", "type": "DYNAMIC", "pose": pose_L, "ja_dur": JA_WAIT_DEFAULT, "interval": 1.7, "nod_check": lambda y, p: y <= 15.0 and p < -15.0, "shake_check": lambda y, p: y > 15.0 and p < -15.0},
        "5": {"name": "C_Rev", "type": "DYNAMIC", "pose": pose_C, "ja_dur": JA_WAIT_DEFAULT, "interval": 1.7, "nod_check": lambda y, p: (y >= 15.0 or y <= -15.0) and p < -15.0, "shake_check": lambda y, p: -15.0 < y < 15.0 and p < -15.0},
        "6": {"name": "R_Rev", "type": "DYNAMIC", "pose": pose_R, "ja_dur": JA_WAIT_DEFAULT, "interval": 1.7, "nod_check": lambda y, p: y >= -15.0 and p < -15.0, "shake_check": lambda y, p: y < -15.0 and p < -15.0},
        "7": {"name": "L_None", "type": "NONE", "pose": pose_L, "check": lambda y, p: y > 15.0 and p < -15.0, "ja_dur": JA_WAIT_DEFAULT, "interval": 1.7},
        "8": {"name": "C_None", "type": "NONE", "pose": pose_C, "check": lambda y, p: -15.0 < y < 15.0 and p < -15.0, "ja_dur": JA_WAIT_DEFAULT, "interval": 1.7},
        "9": {"name": "R_None", "type": "NONE", "pose": pose_R, "check": lambda y, p: y < -15.0 and p < -15.0, "ja_dur": JA_WAIT_DEFAULT, "interval": 1.7},
        "a": {"name": "MidLC_AnsL", "type": "DYNAMIC", "pose": pose_LC_mid, "ja_dur": JA_WAIT_SHORT, "interval": 1.0, "nod_check": lambda y, p: y > 15.0 and p < -15.0, "shake_check": lambda y, p: y <= 15.0 and p < -15.0},
        "b": {"name": "MidLC_AnsC", "type": "DYNAMIC", "pose": pose_LC_mid, "ja_dur": JA_WAIT_SHORT, "interval": 1.0, "nod_check": lambda y, p: -15.0 < y < 15.0 and p < -15.0, "shake_check": lambda y, p: (y >= 15.0 or y <= -15.0) and p < -15.0},
        "c": {"name": "MidRC_AnsR", "type": "DYNAMIC", "pose": pose_RC_mid, "ja_dur": JA_WAIT_SHORT, "interval": 1.0, "nod_check": lambda y, p: y < -15.0 and p < -15.0, "shake_check": lambda y, p: y >= -15.0 and p < -15.0},
        "d": {"name": "MidRC_AnsC", "type": "DYNAMIC", "pose": pose_RC_mid, "ja_dur": JA_WAIT_SHORT, "interval": 1.0, "nod_check": lambda y, p: -15.0 < y < 15.0 and p < -15.0, "shake_check": lambda y, p: (y >= 15.0 or y <= -15.0) and p < -15.0}
    }

    #通信・状態変数
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 5005))
    sock.settimeout(0.05)

    global current_phase, writer, trial_start_t, active_mode, h_yaw, h_pitch, user_reset_requested
    current_phase = "WAIT_INPUT"; active_mode = None; user_reset_requested = False; reaction_delay_sec = 0.0
    csv_file, writer, trial_start_t = None, None, 0
    h_yaw = h_pitch = 0
    looking_start_t = ja_not_detected_start_t = None

    def get_dynamic_ja_flag():
        is_reaction = any(p in current_phase for p in ["REACTION_DELAY", "REACTION_NODDING", "REACTION_SHAKING", "REACTION_HIDDEN", "COOLDOWN"])
        is_looking = check_is_looking_correct(active_mode, h_yaw, h_pitch)
        return 1 if (is_reaction and is_looking and not user_reset_requested) else 0

    def move_and_record_with_watch(y_rad, p_rad, duration):
        global user_reset_requested
        if duration <= 0: return
        neck.set_angle(y_rad, p_rad, duration, wait=False)
        end_time = time.time() + duration
        while time.time() < end_time:
            try:
                data, _ = sock.recvfrom(1024); globals()['h_yaw'], globals()['h_pitch'] = map(float, data.decode().split(','))
            except socket.timeout: pass
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                if sys.stdin.readline().strip() == "": globals()['user_reset_requested'] = True
            if writer:
                now_elapsed = time.time() - trial_start_t
                target = get_gaze_target(h_yaw, h_pitch); ja_flag = get_dynamic_ja_flag()
                label = current_phase
                if active_mode and active_mode["type"] == "NONE" and label == "REACTION_HIDDEN": label = "POINTING"
                if user_reset_requested: label += "_TAKEN"
                writer.writerow([round(now_elapsed, 4), h_yaw, h_pitch, target, ja_flag, label])

    arm_neck_group.set_named_target("two_arm_waist_standby_pose"); arm_neck_group.go(wait=True)
    rospy.loginfo("Experimental System Ready.")

    try:
        while not rospy.is_shutdown():
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                line = sys.stdin.readline().strip()
                if current_phase != "WAIT_INPUT" and line == "": user_reset_requested = True
                elif current_phase == "WAIT_INPUT":
                    m_key, d_key = None, "1"
                    if line in MODES: m_key = line
                    if m_key:
                        active_mode = MODES[m_key]; reaction_delay_sec = 0.0; user_reset_requested = False
                        file_prefix = "trial_{}_{}".format(time.strftime("%Y%m%d_%H%M%S"), active_mode["name"])
                        csv_file = open(file_prefix + ".csv", 'w'); writer = csv.writer(csv_file)
                        writer.writerow(["time_sec", "yaw", "pitch", "gaze_target", "ja_flag", "phase"])
                        trial_start_t = time.time(); indicator.show(); current_phase = "BASELINE"

            if user_reset_requested and current_phase != "WAIT_INPUT":
                if writer:
                     t_label = current_phase
                     if active_mode and active_mode["type"] == "NONE" and t_label == "REACTION_HIDDEN": t_label = "POINTING"
                     writer.writerow([round(time.time() - trial_start_t, 4), h_yaw, h_pitch, get_gaze_target(h_yaw, h_pitch), 0, t_label + "_TAKEN"])
                current_phase = "RESETTING"
                arm_neck_group.set_named_target("two_arm_waist_standby_pose"); arm_neck_group.go(wait=False)
                reset_start_t = time.time()
                while time.time() - reset_start_t < 2.5:
                    try:
                        data, _ = sock.recvfrom(1024); h_yaw, h_pitch = map(float, data.decode().split(','))
                    except socket.timeout: pass
                    if writer: writer.writerow([round(time.time() - trial_start_t, 4), h_yaw, h_pitch, get_gaze_target(h_yaw, h_pitch), 0, "RESETTING"])
                if csv_file: csv_file.close(); csv_file = writer = None; indicator.hide(); current_phase = "WAIT_INPUT"; continue

            try:
                data, _ = sock.recvfrom(1024); h_yaw, h_pitch = map(float, data.decode().split(','))
            except socket.timeout: pass
            
            if current_phase != "WAIT_INPUT":
                now_elapsed = time.time() - trial_start_t
                if current_phase == "BASELINE" and now_elapsed > BASELINE_DURATION:
                    arm_neck_group.set_joint_value_target(active_mode["pose"]); arm_neck_group.go(wait=False); current_phase = "MOVING"; looking_start_t = ja_not_detected_start_t = None
                elif current_phase == "MOVING" and now_elapsed > (BASELINE_DURATION + MOVING_DURATION):
                    current_phase = "POINTING"; ja_not_detected_start_t = time.time()

                if current_phase in ["MOVING", "POINTING"]:
                    is_correct_look = check_is_looking_correct(active_mode, h_yaw, h_pitch)
                    if is_correct_look:
                        ja_not_detected_start_t = time.time()
                        if looking_start_t is None: looking_start_t = time.time()
                        elif time.time() - looking_start_t >= active_mode["ja_dur"]:
                            if active_mode["type"] == "DYNAMIC":
                                current_phase = "REACTION_DELAY"; move_and_record_with_watch(active_mode["pose"]["neck_yaw_joint"], active_mode["pose"]["neck_pitch_joint"], reaction_delay_sec)
                                if "Rev" in active_mode["name"] or active_mode["name"] in ["4","5","6"]:
                                    current_phase = "REACTION_SHAKING"; move_and_record_with_watch(0, 0, 0.4); move_and_record_with_watch(math.radians(20.0), 0, 0.25); move_and_record_with_watch(math.radians(-20.0), 0, 0.25); move_and_record_with_watch(0, 0, 0.25)
                                else:
                                    current_phase = "REACTION_NODDING"; move_and_record_with_watch(0, 0, 0.4); move_and_record_with_watch(0, math.radians(-30), 0.25); move_and_record_with_watch(0, 0, 0.25)
                                current_phase = "MOVING"; move_and_record_with_watch(active_mode["pose"]["neck_yaw_joint"], active_mode["pose"]["neck_pitch_joint"], 0.4)
                                current_phase = "POINTING"; move_and_record_with_watch(active_mode["pose"]["neck_yaw_joint"], active_mode["pose"]["neck_pitch_joint"], active_mode["interval"])
                            else: 
                                current_phase = "REACTION_HIDDEN"; move_and_record_with_watch(active_mode["pose"]["neck_yaw_joint"], active_mode["pose"]["neck_pitch_joint"], 1.0)
                                current_phase = "POINTING"; move_and_record_with_watch(active_mode["pose"]["neck_yaw_joint"], active_mode["pose"]["neck_pitch_joint"], 0.4 + active_mode["interval"])
                            looking_start_t = None; ja_not_detected_start_t = time.time()
                    else:
                        looking_start_t = None
                        if active_mode["type"] == "DYNAMIC" and current_phase == "POINTING" and h_pitch < -15.0:
                            if ja_not_detected_start_t and time.time() - ja_not_detected_start_t >= JA_TIMEOUT_DURATION:
                                current_phase = "REACTION_DELAY"; move_and_record_with_watch(active_mode["pose"]["neck_yaw_joint"], active_mode["pose"]["neck_pitch_joint"], reaction_delay_sec)
                                if "Rev" in active_mode["name"] or active_mode["name"] in ["4","5","6"]:
                                    current_phase = "REACTION_NODDING"; move_and_record_with_watch(0, 0, 0.4); move_and_record_with_watch(0, math.radians(-30), 0.25); move_and_record_with_watch(0, 0, 0.25)
                                else:
                                    current_phase = "REACTION_SHAKING"; move_and_record_with_watch(0, 0, 0.4); move_and_record_with_watch(math.radians(20.0), 0, 0.25); move_and_record_with_watch(math.radians(-20.0), 0, 0.25); move_and_record_with_watch(0, 0, 0.25)
                                current_phase = "MOVING"; move_and_record_with_watch(active_mode["pose"]["neck_yaw_joint"], active_mode["pose"]["neck_pitch_joint"], 0.4)
                                current_phase = "POINTING"; move_and_record_with_watch(active_mode["pose"]["neck_yaw_joint"], active_mode["pose"]["neck_pitch_joint"], active_mode["interval"])
                                ja_not_detected_start_t = time.time()
                        else: ja_not_detected_start_t = time.time()

                if writer:
                    write_time = time.time() - trial_start_t; target = get_gaze_target(h_yaw, h_pitch); ja_flag = get_dynamic_ja_flag()
                    label = current_phase
                    if active_mode and active_mode["type"] == "NONE" and label == "REACTION_HIDDEN": label = "POINTING"
                    if user_reset_requested: label += "_TAKEN"
                    writer.writerow([round(write_time, 4), h_yaw, h_pitch, target, ja_flag, label])

    finally:
        if csv_file: csv_file.close()
        indicator.stop()
        try:
            rospy.loginfo("Moving to Init Pose...")
            arm_neck_group.set_named_target("two_arm_waist_init_pose"); arm_neck_group.go(wait=True)
        except: pass
        moveit_commander.roscpp_shutdown()

if __name__ == '__main__':
    main()
