import angle_calculator

def _is_joint_available(landmarks, idx_a, idx_b, idx_c):
    try:
        pa = angle_calculator.get_landmark_coord(landmarks[idx_a])
        pb = angle_calculator.get_landmark_coord(landmarks[idx_b])
        pc = angle_calculator.get_landmark_coord(landmarks[idx_c])
        d_ab = (pa[0] - pb[0])**2 + (pa[1] - pb[1])**2 + (pa[2] - pb[2])**2
        d_bc = (pb[0] - pc[0])**2 + (pb[1] - pc[1])**2 + (pb[2] - pc[2])**2
        d_ac = (pa[0] - pc[0])**2 + (pa[1] - pc[1])**2 + (pa[2] - pc[2])**2
        return d_ab > 0.0002 and d_bc > 0.0002 and d_ac > 0.0002
    except Exception:
        return False

def evaluate_stroke(stroke_class_id, landmarks):
    """
    Avalia a biomecânica do golpe baseando-se nos ângulos articulares.
    0 = Forehand, 1 = Backhand, 2 = Saque.
    Retorna uma string de feedback, um dicionário de ângulos e uma lista de juntas com erro (para acionar os 12 LEDs).
    """
    feedback = []
    angles = {}
    failed_joints = []

    if stroke_class_id == 0:  # Forehand
        elbow_angle = angle_calculator.get_elbow_angle(landmarks, side='right')
        angles['elbow_r'] = round(elbow_angle, 1)
        
        if elbow_angle < 120:
            feedback.append("Cotovelo muito flexionado no impacto")
            failed_joints.append("cotovelo_dir")
        elif elbow_angle > 175:
            feedback.append("Braço excessivamente rígido/esticado")
            failed_joints.append("cotovelo_dir")
        else:
            feedback.append("Boa extensão do braço")

        # Avaliação adicional das outras articulações do painel IoT
        if _is_joint_available(landmarks, 24, 12, 14):
            sh_angle = angle_calculator.get_shoulder_angle(landmarks, side='right')
            angles['shoulder_r'] = round(sh_angle, 1)
            if sh_angle < 25.0:
                failed_joints.append("ombro_dir")
                feedback.append("Ombro muito recolhido")

        if _is_joint_available(landmarks, 14, 16, 20):
            w_angle = angle_calculator.get_wrist_angle(landmarks, side='right')
            angles['wrist_r'] = round(w_angle, 1)
            if w_angle < 110.0:
                failed_joints.append("pulso_dir")
                feedback.append("Punho flexionado em excesso")

        if _is_joint_available(landmarks, 12, 24, 26):
            hr = angle_calculator.get_hip_angle(landmarks, side='right')
            if hr < 110.0 or hr > 178.0:
                failed_joints.append("quadril_dir")

        if _is_joint_available(landmarks, 24, 26, 28):
            kr = angle_calculator.get_knee_angle(landmarks, side='right')
            angles['knee_r'] = round(kr, 1)
            if kr > 170.0:
                failed_joints.append("joelho_dir")

        if _is_joint_available(landmarks, 26, 28, 32):
            ar = angle_calculator.get_ankle_angle(landmarks, side='right')
            if ar < 75.0 or ar > 155.0:
                failed_joints.append("tornozelo_dir")
            
    elif stroke_class_id == 1:  # Backhand
        elbow_angle_l = angle_calculator.get_elbow_angle(landmarks, side='left')
        angles['elbow_l'] = round(elbow_angle_l, 1)
        
        if elbow_angle_l < 110:
            feedback.append("Cotovelo muito encolhido")
            failed_joints.append("cotovelo_esq")
        else:
            feedback.append("Braço firme no backhand")

        if _is_joint_available(landmarks, 23, 11, 13):
            sh_l = angle_calculator.get_shoulder_angle(landmarks, side='left')
            angles['shoulder_l'] = round(sh_l, 1)
            if sh_l < 30.0:
                failed_joints.append("ombro_esq")

        if _is_joint_available(landmarks, 13, 15, 19):
            wl = angle_calculator.get_wrist_angle(landmarks, side='left')
            angles['wrist_l'] = round(wl, 1)
            if wl < 115.0 or wl > 178.0:
                failed_joints.append("pulso_esq")

        if _is_joint_available(landmarks, 11, 23, 25):
            hl = angle_calculator.get_hip_angle(landmarks, side='left')
            if hl < 110.0 or hl > 178.0:
                failed_joints.append("quadril_esq")

        if _is_joint_available(landmarks, 23, 25, 27):
            kl = angle_calculator.get_knee_angle(landmarks, side='left')
            angles['knee_l'] = round(kl, 1)
            if kl > 170.0:
                failed_joints.append("joelho_esq")

        if _is_joint_available(landmarks, 25, 27, 31):
            al = angle_calculator.get_ankle_angle(landmarks, side='left')
            if al < 75.0 or al > 155.0:
                failed_joints.append("tornozelo_esq")
            
    elif stroke_class_id == 2:  # Saque
        knee_angle_r = angle_calculator.get_knee_angle(landmarks, side='right')
        knee_angle_l = angle_calculator.get_knee_angle(landmarks, side='left')
        angles['knee_r'] = round(knee_angle_r, 1)
        angles['knee_l'] = round(knee_angle_l, 1)
        
        avg_knee = (knee_angle_r + knee_angle_l) / 2.0
        if avg_knee > 150:
            feedback.append("Dobre mais os joelhos (flexão pobre)")
            failed_joints.extend(["joelho_dir", "joelho_esq"])
        else:
            feedback.append("Boa flexão para impulsão do saque")

        elbow_r = angle_calculator.get_elbow_angle(landmarks, side='right')
        angles['elbow_r'] = round(elbow_r, 1)
        if elbow_r < 135.0:
            failed_joints.append("cotovelo_dir")
            feedback.append("Estenda o braço mais no alto")

        if _is_joint_available(landmarks, 24, 12, 14):
            sh_r = angle_calculator.get_shoulder_angle(landmarks, side='right')
            angles['shoulder_r'] = round(sh_r, 1)
            if sh_r < 85.0:
                failed_joints.append("ombro_dir")

        if _is_joint_available(landmarks, 14, 16, 20):
            wr = angle_calculator.get_wrist_angle(landmarks, side='right')
            if wr < 110.0 or wr > 178.0:
                failed_joints.append("pulso_dir")

        if _is_joint_available(landmarks, 12, 24, 26):
            hr = angle_calculator.get_hip_angle(landmarks, side='right')
            if hr < 120.0 or hr > 178.0:
                failed_joints.append("quadril_dir")

        if _is_joint_available(landmarks, 26, 28, 32):
            ar = angle_calculator.get_ankle_angle(landmarks, side='right')
            if ar < 80.0 or ar > 165.0:
                failed_joints.append("tornozelo_dir")
            
    else:
        feedback.append("Aguardando golpe válido...")
        
    return " | ".join(feedback), angles, sorted(list(set(failed_joints)))
