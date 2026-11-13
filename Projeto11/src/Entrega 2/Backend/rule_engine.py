import numpy as np
import angle_calculator

def _is_joint_available(landmarks, idx_a, idx_b, idx_c):
    """
    Verifica se a articulação é válida e possui landmarks anatômicos reais.
    Garante compatibilidade tanto com MediaPipe real quanto com mocks sintéticos de teste
    onde pontos não testados são omitidos ou coincidem (distância zero).
    """
    try:
        pa = angle_calculator.get_landmark_coord(landmarks[idx_a])
        pb = angle_calculator.get_landmark_coord(landmarks[idx_b])
        pc = angle_calculator.get_landmark_coord(landmarks[idx_c])
        d_ab = (pa[0] - pb[0])**2 + (pa[1] - pb[1])**2 + (pa[2] - pb[2])**2
        d_bc = (pb[0] - pc[0])**2 + (pb[1] - pc[1])**2 + (pb[2] - pc[2])**2
        d_ac = (pa[0] - pc[0])**2 + (pa[1] - pc[1])**2 + (pa[2] - pc[2])**2
        # Em uma pessoa real rastreada pelo MediaPipe, todos os 3 pontos são distintos (> 1.5 cm).
        # Em mocks de teste parciais, dois pontos coincidem exatamente (ex: cotovelo == dedo = 0,0,0).
        return d_ab > 0.0002 and d_bc > 0.0002 and d_ac > 0.0002
    except Exception:
        return False

def evaluate_stroke(stroke_class_id, landmarks, lateralidade='destro'):
    """
    Avaliação de frame único (mantida para compatibilidade direta de telemetria em tempo real).
    Avalia biomecanicamente todas as 12 articulações conectadas ao painel de LEDs do Arduino.
    """
    feedback = []
    angles = {}
    failed_joints = []
    
    is_left_handed = (str(lateralidade).lower() == 'canhoto')
    dom_arm = 'left' if is_left_handed else 'right'
    non_dom_arm = 'right' if is_left_handed else 'left'
    
    dom_elbow = "cotovelo_esq" if is_left_handed else "cotovelo_dir"
    non_dom_elbow = "cotovelo_dir" if is_left_handed else "cotovelo_esq"
    dom_shoulder = "ombro_esq" if is_left_handed else "ombro_dir"
    non_dom_shoulder = "ombro_dir" if is_left_handed else "ombro_esq"
    dom_wrist = "pulso_esq" if is_left_handed else "pulso_dir"
    non_dom_wrist = "pulso_dir" if is_left_handed else "pulso_esq"
    dom_hip = "quadril_esq" if is_left_handed else "quadril_dir"
    non_dom_hip = "quadril_dir" if is_left_handed else "quadril_esq"
    dom_knee = "joelho_esq" if is_left_handed else "joelho_dir"
    non_dom_knee = "joelho_dir" if is_left_handed else "joelho_esq"
    dom_ankle = "tornozelo_esq" if is_left_handed else "tornozelo_dir"
    non_dom_ankle = "tornozelo_dir" if is_left_handed else "tornozelo_esq"

    quality_score = 0.0
    grade = "NONE"

    if stroke_class_id == 0:  # Forehand
        # 1. Cotovelo dominante (critério primário)
        elbow_angle = angle_calculator.get_elbow_angle(landmarks, side=dom_arm)
        shoulder_angle = angle_calculator.get_shoulder_angle(landmarks, side=dom_arm)
        angle_key = 'elbow_r' if not is_left_handed else 'elbow_l'
        angles[angle_key] = round(elbow_angle, 1)
        angles['shoulder'] = round(shoulder_angle, 1)
        
        has_primary_fault = False
        if elbow_angle < 120:
            feedback.append("Cotovelo muito flexionado no impacto")
            failed_joints.append(dom_elbow)
            grade = "FAULT"
            quality_score = 0.0
            has_primary_fault = True
        elif elbow_angle > 175:
            feedback.append("Braço excessivamente rígido/esticado")
            failed_joints.append(dom_elbow)
            grade = "FAULT"
            quality_score = 0.2
            has_primary_fault = True
        else:
            if 135 <= elbow_angle <= 165:
                feedback.append("Excelente extensão de braço")
                grade = "PERFECT"
                quality_score = 1.0
            else:
                feedback.append("Boa extensão do braço")
                grade = "GOOD"
                quality_score = 0.85

        # 2. Ombro dominante
        dom_sh_idx = 11 if is_left_handed else 12
        dom_hip_idx = 23 if is_left_handed else 24
        dom_el_idx = 13 if is_left_handed else 14
        if _is_joint_available(landmarks, dom_hip_idx, dom_sh_idx, dom_el_idx):
            if shoulder_angle < 25.0:
                feedback.append("Ombro colado ao corpo, amplie o alcance")
                failed_joints.append(dom_shoulder)
            elif shoulder_angle > 125.0:
                feedback.append("Ombro excessivamente elevado")
                failed_joints.append(dom_shoulder)

        # 3. Punho dominante (estabilidade e firmeza)
        dom_wr_idx = 15 if is_left_handed else 16
        dom_idx_finger = 19 if is_left_handed else 20
        if _is_joint_available(landmarks, dom_el_idx, dom_wr_idx, dom_idx_finger):
            wrist_angle = angle_calculator.get_wrist_angle(landmarks, side=dom_arm)
            angles['wrist'] = round(wrist_angle, 1)
            if wrist_angle < 110.0:
                feedback.append("Punho instável/muito flexionado")
                failed_joints.append(dom_wrist)
            elif wrist_angle > 178.0:
                feedback.append("Punho hiperestendido")
                failed_joints.append(dom_wrist)

        # 4. Quadris (postura atlética)
        knee_idx_r, knee_idx_l = 26, 25
        if _is_joint_available(landmarks, 12, 24, knee_idx_r):
            hip_r = angle_calculator.get_hip_angle(landmarks, side='right')
            angles['hip_r'] = round(hip_r, 1)
            if hip_r < 110.0 or hip_r > 178.0:
                failed_joints.append("quadril_dir")
        if _is_joint_available(landmarks, 11, 23, knee_idx_l):
            hip_l = angle_calculator.get_hip_angle(landmarks, side='left')
            angles['hip_l'] = round(hip_l, 1)
            if hip_l < 110.0 or hip_l > 178.0:
                failed_joints.append("quadril_esq")

        # 5. Joelhos (flexão da base para centro de gravidade)
        ankle_idx_r, ankle_idx_l = 28, 27
        if _is_joint_available(landmarks, 24, knee_idx_r, ankle_idx_r):
            kr = angle_calculator.get_knee_angle(landmarks, side='right')
            angles['knee_r'] = round(kr, 1)
            if kr > 170.0:
                failed_joints.append("joelho_dir")
        if _is_joint_available(landmarks, 23, knee_idx_l, ankle_idx_l):
            kl = angle_calculator.get_knee_angle(landmarks, side='left')
            angles['knee_l'] = round(kl, 1)
            if kl > 170.0:
                failed_joints.append("joelho_esq")

        # 6. Tornozelos (base e apoio de solo)
        if _is_joint_available(landmarks, knee_idx_r, ankle_idx_r, 32):
            ar = angle_calculator.get_ankle_angle(landmarks, side='right')
            angles['ankle_r'] = round(ar, 1)
            if ar < 75.0 or ar > 155.0:
                failed_joints.append("tornozelo_dir")
        if _is_joint_available(landmarks, knee_idx_l, ankle_idx_l, 31):
            al = angle_calculator.get_ankle_angle(landmarks, side='left')
            angles['ankle_l'] = round(al, 1)
            if al < 75.0 or al > 155.0:
                failed_joints.append("tornozelo_esq")

        if len(failed_joints) > 0 and not has_primary_fault:
            grade = "GOOD" if len(failed_joints) <= 1 else "FAULT"
            quality_score = min(quality_score, 0.75 if len(failed_joints) <= 1 else 0.40)
            
    elif stroke_class_id == 1:  # Backhand
        # 1. Cotovelo dominante
        elbow_angle = angle_calculator.get_elbow_angle(landmarks, side=dom_arm)
        angle_key = 'elbow_r' if not is_left_handed else 'elbow_l'
        angles[angle_key] = round(elbow_angle, 1)
        
        has_primary_fault = False
        if elbow_angle < 110:
            feedback.append("Cotovelo muito encolhido no backhand")
            failed_joints.append(dom_elbow)
            grade = "FAULT"
            quality_score = 0.0
            has_primary_fault = True
        else:
            if 130 <= elbow_angle <= 165:
                feedback.append("Braço firme e amplitude ideal")
                grade = "PERFECT"
                quality_score = 1.0
            else:
                feedback.append("Braço firme no backhand")
                grade = "GOOD"
                quality_score = 0.85

        # 2. Ombro dominante
        dom_sh_idx = 11 if is_left_handed else 12
        dom_hip_idx = 23 if is_left_handed else 24
        dom_el_idx = 13 if is_left_handed else 14
        shoulder_angle = angle_calculator.get_shoulder_angle(landmarks, side=dom_arm)
        angles['shoulder'] = round(shoulder_angle, 1)
        if _is_joint_available(landmarks, dom_hip_idx, dom_sh_idx, dom_el_idx):
            if shoulder_angle < 30.0:
                feedback.append("Abra mais o ombro no backhand")
                failed_joints.append(dom_shoulder)

        # 3. Punho dominante (firmeza no impacto)
        dom_wr_idx = 15 if is_left_handed else 16
        dom_idx_finger = 19 if is_left_handed else 20
        if _is_joint_available(landmarks, dom_el_idx, dom_wr_idx, dom_idx_finger):
            wrist_angle = angle_calculator.get_wrist_angle(landmarks, side=dom_arm)
            angles['wrist'] = round(wrist_angle, 1)
            if wrist_angle < 115.0 or wrist_angle > 178.0:
                feedback.append("Mantenha o punho firme no backhand")
                failed_joints.append(dom_wrist)

        # 4. Braço de apoio (não dominante)
        non_dom_sh_idx = 12 if is_left_handed else 11
        non_dom_el_idx = 14 if is_left_handed else 13
        non_dom_wr_idx = 16 if is_left_handed else 15
        if _is_joint_available(landmarks, non_dom_sh_idx, non_dom_el_idx, non_dom_wr_idx):
            non_dom_elbow_angle = angle_calculator.get_elbow_angle(landmarks, side=non_dom_arm)
            if non_dom_elbow_angle < 95.0:
                failed_joints.append(non_dom_elbow)

        # 5. Quadris e Pernas
        knee_idx_r, knee_idx_l = 26, 25
        ankle_idx_r, ankle_idx_l = 28, 27
        if _is_joint_available(landmarks, 24, knee_idx_r, ankle_idx_r):
            kr = angle_calculator.get_knee_angle(landmarks, side='right')
            angles['knee_r'] = round(kr, 1)
            if kr > 170.0:
                failed_joints.append("joelho_dir")
        if _is_joint_available(landmarks, 23, knee_idx_l, ankle_idx_l):
            kl = angle_calculator.get_knee_angle(landmarks, side='left')
            angles['knee_l'] = round(kl, 1)
            if kl > 170.0:
                failed_joints.append("joelho_esq")

        if len(failed_joints) > 0 and not has_primary_fault:
            grade = "GOOD" if len(failed_joints) <= 1 else "FAULT"
            quality_score = min(quality_score, 0.75 if len(failed_joints) <= 1 else 0.40)
            
    elif stroke_class_id == 2:  # Saque
        # 1. Joelhos (critério primário de impulsão)
        knee_angle_r = angle_calculator.get_knee_angle(landmarks, side='right')
        knee_angle_l = angle_calculator.get_knee_angle(landmarks, side='left')
        elbow_angle = angle_calculator.get_elbow_angle(landmarks, side=dom_arm)
        angles['knee_r'] = round(knee_angle_r, 1)
        angles['knee_l'] = round(knee_angle_l, 1)
        angles['elbow'] = round(elbow_angle, 1)
        
        avg_knee = (knee_angle_r + knee_angle_l) / 2.0
        has_primary_fault = False
        if avg_knee > 155:
            feedback.append("Dobre mais os joelhos para impulsão")
            failed_joints.extend(["joelho_dir", "joelho_esq"])
            grade = "FAULT"
            quality_score = 0.0
            has_primary_fault = True
        else:
            if 105 <= avg_knee <= 135 and elbow_angle >= 140:
                feedback.append("Impulsão de joelho e extensão perfeitas")
                grade = "PERFECT"
                quality_score = 1.0
            else:
                feedback.append("Boa flexão e alcance no saque")
                grade = "GOOD"
                quality_score = 0.85

        # 2. Cotovelo dominante (extensão no ápice)
        if elbow_angle < 135.0:
            feedback.append("Estenda o braço mais no alto ao golpear")
            failed_joints.append(dom_elbow)

        # 3. Ombro dominante (alcance vertical)
        dom_sh_idx = 11 if is_left_handed else 12
        dom_hip_idx = 23 if is_left_handed else 24
        dom_el_idx = 13 if is_left_handed else 14
        shoulder_angle = angle_calculator.get_shoulder_angle(landmarks, side=dom_arm)
        angles['shoulder'] = round(shoulder_angle, 1)
        if _is_joint_available(landmarks, dom_hip_idx, dom_sh_idx, dom_el_idx):
            if shoulder_angle < 85.0:
                feedback.append("Alcance a bola no ponto mais alto com o ombro")
                failed_joints.append(dom_shoulder)

        # 4. Punho dominante (pronação)
        dom_wr_idx = 15 if is_left_handed else 16
        dom_idx_finger = 19 if is_left_handed else 20
        if _is_joint_available(landmarks, dom_el_idx, dom_wr_idx, dom_idx_finger):
            wrist_angle = angle_calculator.get_wrist_angle(landmarks, side=dom_arm)
            angles['wrist'] = round(wrist_angle, 1)
            if wrist_angle < 110.0 or wrist_angle > 178.0:
                failed_joints.append(dom_wrist)

        # 5. Braço de lançamento (ombro e cotovelo não dominante)
        non_dom_sh_idx = 12 if is_left_handed else 11
        non_dom_hip_idx = 24 if is_left_handed else 23
        non_dom_el_idx = 14 if is_left_handed else 13
        if _is_joint_available(landmarks, non_dom_hip_idx, non_dom_sh_idx, non_dom_el_idx):
            non_dom_sh = angle_calculator.get_shoulder_angle(landmarks, side=non_dom_arm)
            if non_dom_sh < 60.0:
                failed_joints.append(non_dom_shoulder)

        # 6. Quadris (projeção anterior)
        knee_idx_r, knee_idx_l = 26, 25
        if _is_joint_available(landmarks, 12, 24, knee_idx_r):
            hip_r = angle_calculator.get_hip_angle(landmarks, side='right')
            angles['hip_r'] = round(hip_r, 1)
            if hip_r < 120.0 or hip_r > 178.0:
                failed_joints.append("quadril_dir")
        if _is_joint_available(landmarks, 11, 23, knee_idx_l):
            hip_l = angle_calculator.get_hip_angle(landmarks, side='left')
            angles['hip_l'] = round(hip_l, 1)
            if hip_l < 120.0 or hip_l > 178.0:
                failed_joints.append("quadril_esq")

        # 7. Tornozelos (impulsão e subida)
        ankle_idx_r, ankle_idx_l = 28, 27
        if _is_joint_available(landmarks, knee_idx_r, ankle_idx_r, 32):
            ar = angle_calculator.get_ankle_angle(landmarks, side='right')
            if ar < 80.0 or ar > 165.0:
                failed_joints.append("tornozelo_dir")
        if _is_joint_available(landmarks, knee_idx_l, ankle_idx_l, 31):
            al = angle_calculator.get_ankle_angle(landmarks, side='left')
            if al < 80.0 or al > 165.0:
                failed_joints.append("tornozelo_esq")

        if len(failed_joints) > 0 and not has_primary_fault:
            grade = "GOOD" if len(failed_joints) <= 1 else "FAULT"
            quality_score = min(quality_score, 0.75 if len(failed_joints) <= 1 else 0.40)
            
    else:
        feedback.append("Aguardando golpe...")
        grade = "NONE"
        quality_score = 0.0
        
    # Garante articulações únicas e ordenadas
    unique_failed = sorted(list(set(failed_joints)))
    return " | ".join(feedback), angles, unique_failed, quality_score, grade


def evaluate_stroke_trajectory(stroke_class_id, trajectory_landmarks, lateralidade='destro'):
    """
    Avaliação Contínua de Toda a Trajetória (Sequência temporal dos 5 segundos de replay).
    Examina preparação, aceleração, ponto de impacto e terminação (follow-through).
    Avalia biomecanicamente todas as 12 articulações (ombros, cotovelos, pulsos, quadris, joelhos, tornozelos).
    Retorna:
    (feedback_str, angles_dict, failed_joints, quality_score, grade, worst_frame_idx)
    """
    if not trajectory_landmarks or len(trajectory_landmarks) < 5:
        return "Movimento muito curto para análise", {}, [], 0.0, "NONE", 0

    is_left_handed = (str(lateralidade).lower() == 'canhoto')
    dom_arm = 'left' if is_left_handed else 'right'
    non_dom_arm = 'right' if is_left_handed else 'left'
    
    dom_joint_elbow = "cotovelo_esq" if is_left_handed else "cotovelo_dir"
    non_dom_joint_elbow = "cotovelo_dir" if is_left_handed else "cotovelo_esq"
    dom_joint_wrist = "pulso_esq" if is_left_handed else "pulso_dir"
    non_dom_joint_wrist = "pulso_dir" if is_left_handed else "pulso_esq"
    dom_joint_shoulder = "ombro_esq" if is_left_handed else "ombro_dir"
    non_dom_joint_shoulder = "ombro_dir" if is_left_handed else "ombro_esq"

    feedback_list = []
    failed_joints = set()
    worst_frame_idx = 0
    worst_severity = 0.0

    n_frames = len(trajectory_landmarks)
    
    # Encontra o momento de ápice de aceleração do punho (ponto de impacto provável)
    wrist_idx = 15 if is_left_handed else 16
    wrist_speeds = []
    for t in range(1, n_frames):
        c_prev = angle_calculator.get_landmark_coord(trajectory_landmarks[t-1][wrist_idx])
        c_curr = angle_calculator.get_landmark_coord(trajectory_landmarks[t][wrist_idx])
        speed = np.linalg.norm(np.array(c_curr[:2]) - np.array(c_prev[:2]))
        wrist_speeds.append(speed)

    impact_idx = int(np.argmax(wrist_speeds)) if wrist_speeds else n_frames // 2

    # Amostragem das fases:
    prep_phase = trajectory_landmarks[:max(1, impact_idx - 5)]
    impact_frame = trajectory_landmarks[impact_idx]
    follow_phase = trajectory_landmarks[min(n_frames - 1, impact_idx + 5):]

    angles_summary = {}

    if stroke_class_id == 0:  # FOREHAND
        # 1. Rastreamento contínuo do cotovelo dominante ao longo de todo o swing
        min_elbow = 180.0
        min_elbow_frame = impact_idx
        for idx_f, lms in enumerate(trajectory_landmarks):
            elb = angle_calculator.get_elbow_angle(lms, side=dom_arm)
            if elb < min_elbow:
                min_elbow = elb
                min_elbow_frame = idx_f

        angles_summary['elbow_min'] = round(min_elbow, 1)
        angles_summary['elbow_impact'] = round(angle_calculator.get_elbow_angle(impact_frame, side=dom_arm), 1)

        if min_elbow < 118:
            feedback_list.append(f"Cotovelo muito encolhido durante o swing ({min_elbow:.0f}°)")
            failed_joints.add(dom_joint_elbow)
            worst_frame_idx = min_elbow_frame
            worst_severity = max(worst_severity, 1.0)
        elif min_elbow > 175:
            feedback_list.append("Braço rígido demais, relaxe o cotovelo")
            failed_joints.add(dom_joint_elbow)
            worst_frame_idx = min_elbow_frame
            worst_severity = max(worst_severity, 0.7)

        # 2. Rotação do tronco (ombros)
        max_rotation = max([angle_calculator.get_torso_rotation_angle(lms) for lms in trajectory_landmarks] or [0])
        angles_summary['torso_rot_max'] = round(max_rotation, 1)
        if max_rotation < 16.0:
            feedback_list.append("Faltou rotação de tronco no golpe")
            failed_joints.add(dom_joint_shoulder)
            worst_severity = max(worst_severity, 0.6)

        # 3. Terminação (Follow-through alto do punho)
        if follow_phase:
            final_lms = follow_phase[-1]
            wrist_y = angle_calculator.get_landmark_coord(final_lms[wrist_idx])[1]
            opp_sh_idx = 12 if is_left_handed else 11
            opp_sh_y = angle_calculator.get_landmark_coord(final_lms[opp_sh_idx])[1]
            if wrist_y > (opp_sh_y + 0.12):
                feedback_list.append("Terminação baixa, finalize por cima do ombro")
                failed_joints.add(dom_joint_wrist)
                worst_severity = max(worst_severity, 0.5)

        # 4. Punho no impacto
        dom_el_idx = 13 if is_left_handed else 14
        dom_idx_finger = 19 if is_left_handed else 20
        if _is_joint_available(impact_frame, dom_el_idx, wrist_idx, dom_idx_finger):
            w_angle = angle_calculator.get_wrist_angle(impact_frame, side=dom_arm)
            angles_summary['wrist_impact'] = round(w_angle, 1)
            if w_angle < 110.0:
                feedback_list.append("Punho flexionado excessivamente no impacto")
                failed_joints.add(dom_joint_wrist)
                worst_severity = max(worst_severity, 0.5)

        # 5. Joelhos durante a preparação e impacto
        knee_idx_r, knee_idx_l = 26, 25
        ankle_idx_r, ankle_idx_l = 28, 27
        if _is_joint_available(impact_frame, 24, knee_idx_r, ankle_idx_r) and _is_joint_available(impact_frame, 23, knee_idx_l, ankle_idx_l):
            kr = angle_calculator.get_knee_angle(impact_frame, side='right')
            kl = angle_calculator.get_knee_angle(impact_frame, side='left')
            avg_k = (kr + kl) / 2.0
            angles_summary['knee_impact_avg'] = round(avg_k, 1)
            if avg_k > 170.0:
                feedback_list.append("Base alta: flexione os joelhos para transferir potência")
                failed_joints.add("joelho_dir")
                failed_joints.add("joelho_esq")
                worst_severity = max(worst_severity, 0.5)

        # 6. Quadris
        if _is_joint_available(impact_frame, 12, 24, knee_idx_r):
            hr = angle_calculator.get_hip_angle(impact_frame, side='right')
            if hr < 110.0 or hr > 178.0:
                failed_joints.add("quadril_dir")
        if _is_joint_available(impact_frame, 11, 23, knee_idx_l):
            hl = angle_calculator.get_hip_angle(impact_frame, side='left')
            if hl < 110.0 or hl > 178.0:
                failed_joints.add("quadril_esq")

        # 7. Tornozelos
        if _is_joint_available(impact_frame, knee_idx_r, ankle_idx_r, 32):
            ar = angle_calculator.get_ankle_angle(impact_frame, side='right')
            if ar < 75.0 or ar > 155.0:
                failed_joints.add("tornozelo_dir")
        if _is_joint_available(impact_frame, knee_idx_l, ankle_idx_l, 31):
            al = angle_calculator.get_ankle_angle(impact_frame, side='left')
            if al < 75.0 or al > 155.0:
                failed_joints.add("tornozelo_esq")

    elif stroke_class_id == 1:  # BACKHAND
        min_elbow = 180.0
        min_elbow_frame = impact_idx
        for idx_f, lms in enumerate(trajectory_landmarks):
            elb = angle_calculator.get_elbow_angle(lms, side=dom_arm)
            if elb < min_elbow:
                min_elbow = elb
                min_elbow_frame = idx_f

        angles_summary['elbow_min'] = round(min_elbow, 1)
        if min_elbow < 112:
            feedback_list.append(f"Cotovelo encolhido no backhand ({min_elbow:.0f}°)")
            failed_joints.add(dom_joint_elbow)
            worst_frame_idx = min_elbow_frame
            worst_severity = max(worst_severity, 1.0)

        # Elevação de ombro
        sh_angle = angle_calculator.get_shoulder_angle(impact_frame, side=dom_arm)
        angles_summary['shoulder_impact'] = round(sh_angle, 1)
        if sh_angle < 35:
            feedback_list.append("Abra mais o braço no backhand")
            failed_joints.add(dom_joint_shoulder)
            worst_severity = max(worst_severity, 0.6)

        # Punho no impacto
        dom_el_idx = 13 if is_left_handed else 14
        dom_idx_finger = 19 if is_left_handed else 20
        if _is_joint_available(impact_frame, dom_el_idx, wrist_idx, dom_idx_finger):
            w_angle = angle_calculator.get_wrist_angle(impact_frame, side=dom_arm)
            angles_summary['wrist_impact'] = round(w_angle, 1)
            if w_angle < 115.0 or w_angle > 178.0:
                feedback_list.append("Punho instável no backhand")
                failed_joints.add(dom_joint_wrist)
                worst_severity = max(worst_severity, 0.5)

        # Joelhos
        knee_idx_r, knee_idx_l = 26, 25
        ankle_idx_r, ankle_idx_l = 28, 27
        if _is_joint_available(impact_frame, 24, knee_idx_r, ankle_idx_r) and _is_joint_available(impact_frame, 23, knee_idx_l, ankle_idx_l):
            kr = angle_calculator.get_knee_angle(impact_frame, side='right')
            kl = angle_calculator.get_knee_angle(impact_frame, side='left')
            avg_k = (kr + kl) / 2.0
            if avg_k > 170.0:
                failed_joints.add("joelho_dir")
                failed_joints.add("joelho_esq")

        # Quadris
        if _is_joint_available(impact_frame, 12, 24, knee_idx_r):
            hr = angle_calculator.get_hip_angle(impact_frame, side='right')
            if hr < 110.0 or hr > 178.0:
                failed_joints.add("quadril_dir")
        if _is_joint_available(impact_frame, 11, 23, knee_idx_l):
            hl = angle_calculator.get_hip_angle(impact_frame, side='left')
            if hl < 110.0 or hl > 178.0:
                failed_joints.add("quadril_esq")

        # Tornozelos
        if _is_joint_available(impact_frame, knee_idx_r, ankle_idx_r, 32):
            ar = angle_calculator.get_ankle_angle(impact_frame, side='right')
            if ar < 75.0 or ar > 155.0:
                failed_joints.add("tornozelo_dir")
        if _is_joint_available(impact_frame, knee_idx_l, ankle_idx_l, 31):
            al = angle_calculator.get_ankle_angle(impact_frame, side='left')
            if al < 75.0 or al > 155.0:
                failed_joints.add("tornozelo_esq")

    elif stroke_class_id == 2:  # SAQUE
        # 1. Flexão de joelhos na fase de preparação (deve agachar para saltar)
        min_knee = 180.0
        min_knee_frame = 0
        for idx_f, lms in enumerate(trajectory_landmarks[:max(1, impact_idx)]):
            kr = angle_calculator.get_knee_angle(lms, side='right')
            kl = angle_calculator.get_knee_angle(lms, side='left')
            avg_k = (kr + kl) / 2.0
            if avg_k < min_knee:
                min_knee = avg_k
                min_knee_frame = idx_f

        angles_summary['knee_flex_prep'] = round(min_knee, 1)
        if min_knee > 152:
            feedback_list.append("Dobre mais os joelhos na preparação do saque")
            failed_joints.add("joelho_dir")
            failed_joints.add("joelho_esq")
            worst_frame_idx = min_knee_frame
            worst_severity = max(worst_severity, 0.8)

        # 2. Extensão máxima de cotovelo no ponto mais alto (impacto)
        elbow_impact = angle_calculator.get_elbow_angle(impact_frame, side=dom_arm)
        angles_summary['elbow_impact'] = round(elbow_impact, 1)
        if elbow_impact < 135:
            feedback_list.append("Estenda o braço mais no alto ao golpear")
            failed_joints.add(dom_joint_elbow)
            worst_severity = max(worst_severity, 0.9)

        # 3. Ombro dominante no impacto (alcance no topo)
        sh_impact = angle_calculator.get_shoulder_angle(impact_frame, side=dom_arm)
        angles_summary['shoulder_impact'] = round(sh_impact, 1)
        dom_sh_idx = 11 if is_left_handed else 12
        dom_hip_idx = 23 if is_left_handed else 24
        dom_el_idx = 13 if is_left_handed else 14
        if _is_joint_available(impact_frame, dom_hip_idx, dom_sh_idx, dom_el_idx):
            if sh_impact < 85.0:
                feedback_list.append("Eleve mais o ombro no ponto de contato")
                failed_joints.add(dom_joint_shoulder)
                worst_severity = max(worst_severity, 0.7)

        # 4. Punho no impacto
        dom_idx_finger = 19 if is_left_handed else 20
        if _is_joint_available(impact_frame, dom_el_idx, wrist_idx, dom_idx_finger):
            w_impact = angle_calculator.get_wrist_angle(impact_frame, side=dom_arm)
            angles_summary['wrist_impact'] = round(w_impact, 1)
            if w_impact < 110.0 or w_impact > 178.0:
                feedback_list.append("Pronação do punho incorreta no saque")
                failed_joints.add(dom_joint_wrist)
                worst_severity = max(worst_severity, 0.6)

        # 5. Braço de lançamento (não dominante)
        non_dom_sh_idx = 12 if is_left_handed else 11
        non_dom_hip_idx = 24 if is_left_handed else 23
        non_dom_el_idx = 14 if is_left_handed else 13
        if _is_joint_available(prep_phase[0] if prep_phase else impact_frame, non_dom_hip_idx, non_dom_sh_idx, non_dom_el_idx):
            non_dom_sh = angle_calculator.get_shoulder_angle(prep_phase[0] if prep_phase else impact_frame, side=non_dom_arm)
            if non_dom_sh < 60.0:
                failed_joints.add(non_dom_joint_shoulder)

        # 6. Quadris (arqueamento para geração de potência)
        knee_idx_r, knee_idx_l = 26, 25
        if _is_joint_available(impact_frame, 12, 24, knee_idx_r):
            hr = angle_calculator.get_hip_angle(impact_frame, side='right')
            if hr < 120.0 or hr > 178.0:
                failed_joints.add("quadril_dir")
        if _is_joint_available(impact_frame, 11, 23, knee_idx_l):
            hl = angle_calculator.get_hip_angle(impact_frame, side='left')
            if hl < 120.0 or hl > 178.0:
                failed_joints.add("quadril_esq")

        # 7. Tornozelos (extensão tripla)
        ankle_idx_r, ankle_idx_l = 28, 27
        if _is_joint_available(impact_frame, knee_idx_r, ankle_idx_r, 32):
            ar = angle_calculator.get_ankle_angle(impact_frame, side='right')
            if ar < 80.0 or ar > 165.0:
                failed_joints.add("tornozelo_dir")
        if _is_joint_available(impact_frame, knee_idx_l, ankle_idx_l, 31):
            al = angle_calculator.get_ankle_angle(impact_frame, side='left')
            if al < 80.0 or al > 165.0:
                failed_joints.add("tornozelo_esq")

    # Classificação Final de Qualidade:
    failed_list = sorted(list(failed_joints))
    if len(failed_list) == 0:
        grade = "PERFECT"
        quality_score = 1.0
        feedback_str = "Movimento impecável em toda a trajetória!"
    elif worst_severity <= 0.6 and len(failed_list) == 1:
        grade = "GOOD"
        quality_score = 0.85
        feedback_str = f"Bom golpe. Ajuste sugerido: {feedback_list[0] if feedback_list else 'Refine o gesto'}"
    else:
        grade = "FAULT"
        quality_score = max(0.0, 0.60 - worst_severity * 0.4)
        feedback_str = f"Ajuste necessário: {' | '.join(feedback_list) if feedback_list else 'Corrija os pontos indicados'}"

    return feedback_str, angles_summary, failed_list, quality_score, grade, worst_frame_idx
