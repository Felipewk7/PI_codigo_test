import numpy as np

def calculate_angle(a, b, c):
    """
    Calcula o ângulo em graus entre 3 pontos (x, y, z) onde 'b' é o vértice.
    """
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    c = np.array(c, dtype=np.float32)
    
    ba = a - b
    bc = c - b
    
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return 180.0
        
    cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    
    return float(np.degrees(angle))

def get_landmark_coord(landmark):
    """Extrai [x, y, z] do objeto landmark do MediaPipe Tasks API."""
    if hasattr(landmark, 'x'):
        return [landmark.x, landmark.y, landmark.z]
    elif isinstance(landmark, (list, tuple, np.ndarray)):
        return [float(landmark[0]), float(landmark[1]), float(landmark[2]) if len(landmark) > 2 else 0.0]
    return [0.0, 0.0, 0.0]

def get_elbow_angle(landmarks, side='right'):
    """Calcula o ângulo do cotovelo."""
    if side == 'right':
        a = get_landmark_coord(landmarks[12])
        b = get_landmark_coord(landmarks[14])
        c = get_landmark_coord(landmarks[16])
    else:
        a = get_landmark_coord(landmarks[11])
        b = get_landmark_coord(landmarks[13])
        c = get_landmark_coord(landmarks[15])
    return calculate_angle(a, b, c)

def get_shoulder_angle(landmarks, side='right'):
    """Calcula o ângulo de elevação do ombro (Quadril -> Ombro -> Cotovelo)."""
    if side == 'right':
        a = get_landmark_coord(landmarks[24])
        b = get_landmark_coord(landmarks[12])
        c = get_landmark_coord(landmarks[14])
    else:
        a = get_landmark_coord(landmarks[23])
        b = get_landmark_coord(landmarks[11])
        c = get_landmark_coord(landmarks[13])
    return calculate_angle(a, b, c)

def get_knee_angle(landmarks, side='right'):
    """Calcula o ângulo do joelho."""
    if side == 'right':
        a = get_landmark_coord(landmarks[24])
        b = get_landmark_coord(landmarks[26])
        c = get_landmark_coord(landmarks[28])
    else:
        a = get_landmark_coord(landmarks[23])
        b = get_landmark_coord(landmarks[25])
        c = get_landmark_coord(landmarks[27])
    return calculate_angle(a, b, c)

def get_wrist_angle(landmarks, side='right'):
    """Calcula o ângulo do punho (Cotovelo -> Pulso -> Dedo Indicador)."""
    if side == 'right':
        a = get_landmark_coord(landmarks[14])
        b = get_landmark_coord(landmarks[16])
        c = get_landmark_coord(landmarks[20])
    else:
        a = get_landmark_coord(landmarks[13])
        b = get_landmark_coord(landmarks[15])
        c = get_landmark_coord(landmarks[19])
    return calculate_angle(a, b, c)

def get_hip_angle(landmarks, side='right'):
    """Calcula o ângulo de flexão do quadril (Ombro -> Quadril -> Joelho)."""
    if side == 'right':
        a = get_landmark_coord(landmarks[12])
        b = get_landmark_coord(landmarks[24])
        c = get_landmark_coord(landmarks[26])
    else:
        a = get_landmark_coord(landmarks[11])
        b = get_landmark_coord(landmarks[23])
        c = get_landmark_coord(landmarks[25])
    return calculate_angle(a, b, c)

def get_ankle_angle(landmarks, side='right'):
    """Calcula o ângulo do tornozelo (Joelho -> Tornozelo -> Ponta do Pé)."""
    if side == 'right':
        a = get_landmark_coord(landmarks[26])
        b = get_landmark_coord(landmarks[28])
        c = get_landmark_coord(landmarks[32])
    else:
        a = get_landmark_coord(landmarks[25])
        b = get_landmark_coord(landmarks[27])
        c = get_landmark_coord(landmarks[31])
    return calculate_angle(a, b, c)
