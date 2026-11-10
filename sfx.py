"""
sfx.py - gera de graca, sem baixar nada, os efeitos sonoros e uma musica de fundo ambiente.

    python sfx.py            cria audio/sfx/*.wav (whoosh, impacto, pop, tick, riser, carimbo)
    python sfx.py --musica   cria 3 trilhas em musicas/ (tensa, epica e calma), em loop perfeito

Tudo e sintetizado por codigo (sem direitos autorais). Se voce tiver musicas suas
(mp3/wav) coloque na pasta musicas e o sistema usa elas no lugar da gerada.
"""
import os
import sys

import numpy as np
import soundfile as sf

SR = 44100
RNG = np.random.default_rng(11)


def t_(seg):
    return np.arange(int(SR * seg)) / SR


def normaliza(x, pico=0.9):
    m = float(np.max(np.abs(x))) or 1.0
    return (x / m * pico).astype(np.float32)


def passa_baixa_var(x, cortes):
    """filtro de um polo com frequencia de corte variando no tempo"""
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        a = 1 - np.exp(-2 * np.pi * cortes[i] / SR)
        acc += a * (x[i] - acc)
        y[i] = acc
    return y


def whoosh():
    """Deslize suave de ar (transicao): curto, sem grave estourando, pico no meio."""
    t = t_(0.42)
    ruido = RNG.standard_normal(len(t))
    corte = 900 * (4.5 ** (t / t[-1]))                    # 900 Hz -> 4 kHz
    y = passa_baixa_var(ruido, corte)
    y = y - passa_baixa_var(y, np.full(len(t), 700.0))     # tira todo o grave (sem "ronco")
    y = passa_baixa_var(y, np.full(len(t), 5200.0))        # tira o chiado agudo
    x = t / t[-1]
    env = np.sin(np.pi * np.clip(x ** 0.8, 0, 1)) ** 2.2   # sobe e desce sem estalo
    return normaliza(y * env, 0.55)


def impacto():
    t = t_(1.5)
    f = 35 + 60 * np.exp(-t * 14)
    fase = 2 * np.pi * np.cumsum(f) / SR
    boom = np.sin(fase) * np.exp(-t * 3.2)
    ruido = passa_baixa_var(RNG.standard_normal(len(t)), np.full(len(t), 1800.0)) * np.exp(-t * 28)
    cauda = passa_baixa_var(RNG.standard_normal(len(t)), np.full(len(t), 400.0)) * np.exp(-t * 3.0) * 0.18
    return normaliza(boom + 0.7 * ruido + cauda, 0.95)


def pop():
    t = t_(0.18)
    f = 420 + 700 * np.exp(-t * 40)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 28)
    return normaliza(y, 0.6)


def tick():
    t = t_(0.07)
    y = np.sin(2 * np.pi * 2300 * t) * np.exp(-t * 90) + 0.2 * RNG.standard_normal(len(t)) * np.exp(-t * 200)
    return normaliza(y, 0.5)


def riser():
    t = t_(2.2)
    ruido = RNG.standard_normal(len(t))
    corte = 200 * (30 ** (t / t[-1]))
    y = passa_baixa_var(ruido, corte)
    tom = np.sin(2 * np.pi * np.cumsum(120 * (8 ** (t / t[-1]))) / SR) * 0.25
    env = (t / t[-1]) ** 2.2
    y = (y + tom) * env
    y[-int(SR * 0.02):] *= np.linspace(1, 0, int(SR * 0.02))
    return normaliza(y, 0.8)


def carimbo():
    t = t_(0.55)
    f = 55 + 120 * np.exp(-t * 40)
    corpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
    clack = passa_baixa_var(RNG.standard_normal(len(t)), np.full(len(t), 4500.0)) * np.exp(-t * 90)
    return normaliza(corpo + 0.6 * clack, 0.95)


def clique():
    """clique de mouse/toque: 'tec' seco + um toque mais agudo logo depois"""
    t = t_(0.16)
    y = np.zeros(len(t))
    for ini, f, g in ((0.0, 1500, 1.0), (0.075, 2400, 0.6)):
        i0 = int(SR * ini)
        tt = t[: len(t) - i0]
        y[i0:] += (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 140)
                   + 0.5 * RNG.standard_normal(len(tt)) * np.exp(-tt * 260)) * g
    return normaliza(y, 0.55)


def brilho():
    """brilho/estrelinha: notas agudas em sequencia rapida com cauda suave"""
    t = t_(0.9)
    y = np.zeros(len(t))
    for k, f in enumerate((1568, 2093, 2637, 3136)):
        i0 = int(SR * 0.055 * k)
        tt = t[: len(t) - i0]
        y[i0:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 6.5) * (0.9 - 0.12 * k)
    y += 0.2 * np.sin(2 * np.pi * 784 * t) * np.exp(-t * 5)
    return normaliza(y, 0.5)


def drone():
    """grave sombrio que sobe e some (abre cenas serias)"""
    t = t_(2.4)
    y = sum(np.sin(2 * np.pi * f * t + k) * g for k, (f, g) in enumerate(((46, 1.0), (69, 0.5), (92.3, 0.3))))
    y += 0.15 * passa_baixa_var(RNG.standard_normal(len(t)), np.full(len(t), 300.0))
    env = np.minimum(1, t / 0.5) * np.exp(-np.maximum(0, t - 0.5) * 1.6)
    return normaliza(y * env, 0.7)


def subhit():
    """batida grave de documentario, no momento de uma revelacao"""
    t = t_(1.1)
    f = 38 + 90 * np.exp(-t * 28)
    corpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.2)
    estalo = passa_baixa_var(RNG.standard_normal(len(t)), np.full(len(t), 900.0)) * np.exp(-t * 40) * 0.5
    return normaliza(corpo + estalo, 0.95)


def projetor():
    """clique de projetor de filme"""
    t = t_(0.14)
    y = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 70) + 0.8 * passa_baixa_var(RNG.standard_normal(len(t)), np.full(len(t), 3000.0)) * np.exp(-t * 110)
    return normaliza(y, 0.5)


def papel():
    """farfalhar de papel / foto sendo colocada na mesa"""
    t = t_(0.35)
    r = RNG.standard_normal(len(t))
    y = passa_baixa_var(r, np.full(len(t), 6000.0)) - passa_baixa_var(r, np.full(len(t), 1500.0))
    env = np.exp(-t * 14) * (0.6 + 0.4 * np.abs(np.sin(t * 60)))
    return normaliza(y * env, 0.45)


def gerar_efeitos():
    os.makedirs("audio/sfx", exist_ok=True)
    for nome, fn in [("whoosh", whoosh), ("impacto", impacto), ("pop", pop),
                     ("tick", tick), ("riser", riser), ("carimbo", carimbo),
                     ("clique", clique), ("brilho", brilho),
                     ("drone", drone), ("subhit", subhit), ("projetor", projetor), ("papel", papel)]:
        sf.write(f"audio/sfx/{nome}.wav", fn(), SR, subtype="PCM_16")
        print("  criado audio/sfx/%s.wav" % nome)


def _midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


ACORDES = {
    "Am": [45, 52, 57, 60, 64], "F": [41, 48, 53, 57, 60], "C": [48, 55, 60, 64, 67],
    "G": [43, 50, 55, 59, 62], "Dm": [38, 50, 53, 57, 62], "E": [40, 47, 52, 56, 59],
}
ESTILOS = {
    # nome: (progressao, bpm, batida grave, arpejo, brilho do pad)
    "tensa": (["Am", "F", "Dm", "E"], 90, "meia", True, 1100),
    "epica": (["Am", "F", "C", "G"], 100, "cheia", True, 1700),
    "calma": (["C", "G", "Am", "F"], 80, "nenhuma", True, 1300),
}


def musica_estilo(nome):
    """Trilha de documentario com acordes, arpejo, batida e reverb. Loop perfeito (reverb circular)."""
    from scipy.signal import butter, sosfilt
    prog, bpm, batida, arpejo, brilho = ESTILOS[nome]
    beat = 60.0 / bpm
    compasso = 4 * beat
    L = 16 * compasso                      # 16 compassos; cada acorde dura 2 compassos
    n = int(SR * L)
    t = np.arange(n) / SR
    seg = 2 * compasso
    pad = np.zeros(n)
    cauda = int(SR * 1.5)
    buf = np.zeros(n + cauda)
    tb = np.arange(n + cauda) / SR
    for k in range(8):                     # 8 acordes (a progressao repete 2 vezes)
        acorde = ACORDES[prog[k % len(prog)]]
        ini = k * seg
        # janela suave: sobe 1,2 s antes, desce 1,2 s depois do fim do segmento
        w = np.interp(tb, [ini - 1.2, ini + 0.4, ini + seg - 0.4, ini + seg + 1.2], [0, 1, 1, 0], left=0, right=0)
        w = np.sin(np.clip(w, 0, 1) * np.pi / 2) ** 2
        for j, m in enumerate(acorde):
            for cents in (-4, 0, 4):
                f0 = _midi(m) * 2 ** (cents / 1200)
                for h in range(1, 7):
                    buf += w * (0.5 / h) * np.sin(2 * np.pi * f0 * h * tb + j + h * 0.7) * (0.8 if j else 1.2)
    pad = buf[:n].copy()
    pad[: cauda] += buf[n:]                # dobra o final no comeco (loop sem emenda)
    sos = butter(2, brilho, btype="low", fs=SR, output="sos")
    pad = sosfilt(sos, pad)
    pad /= np.max(np.abs(pad)) or 1

    mix = pad * 0.55
    # arpejo (colcheias) com eco
    if arpejo:
        arp = np.zeros(n)
        passo = beat / 2
        padrao = [0, 2, 1, 2, 3, 2, 1, 2] if nome != "calma" else [0, 2, 3, 2]
        for i in range(int(L / passo)):
            acorde = ACORDES[prog[(int(i * passo // seg)) % len(prog)]]
            nota = acorde[2 + padrao[i % len(padrao)] % 3] + 12
            if nome == "tensa" and i % 4 == 3:
                continue
            i0 = int(i * passo * SR)
            m = int(SR * 0.7)
            tt = np.arange(m) / SR
            f = _midi(nota)
            som = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt) + 0.15 * np.sin(2 * np.pi * 3 * f * tt)) * np.exp(-tt * 6)
            som[: int(SR * 0.004)] *= np.linspace(0, 1, int(SR * 0.004))
            fim = min(n, i0 + m)
            arp[i0:fim] += som[: fim - i0] * (0.8 if i % 2 == 0 else 0.55)
        atraso = int(SR * beat * 0.75)
        eco = arp.copy()
        for rep in range(1, 4):
            eco += np.roll(arp, atraso * rep) * (0.42 ** rep)
        mix += eco / (np.max(np.abs(eco)) or 1) * 0.30
    # batida grave
    if batida != "nenhuma":
        passo_b = beat if batida == "cheia" else 2 * beat
        for i in range(int(L / passo_b)):
            i0 = int(i * passo_b * SR)
            m = int(SR * 0.45)
            tt = np.arange(m) / SR
            f = 42 + 70 * np.exp(-tt * 30)
            k = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9)
            fim = min(n, i0 + m)
            mix[i0:fim] += k[: fim - i0] * (0.55 if batida == "cheia" else 0.4)
    # reverb circular (cauda de 2,6 s) => loop perfeito
    ir_t = np.arange(int(SR * 2.6)) / SR
    ir = RNG.standard_normal(len(ir_t)) * np.exp(-ir_t * 2.4)
    ir = passa_baixa_var(ir, np.full(len(ir), 3500.0))
    IR = np.zeros(n)
    IR[: len(ir)] = ir / np.sqrt(np.sum(ir ** 2))
    molhado = np.fft.irfft(np.fft.rfft(mix) * np.fft.rfft(IR), n)
    y = mix * 0.65 + molhado * 0.45
    return normaliza(y, 0.7)


def gerar_musica():
    os.makedirs("musicas", exist_ok=True)
    for nome in ESTILOS:
        y = musica_estilo(nome)
        sf.write(f"musicas/ambiente_gerada_{nome}.wav", y, SR, subtype="PCM_16")
        print("  criada musicas/ambiente_gerada_%s.wav (loop de %.0f s)" % (nome, len(y) / SR))


if __name__ == "__main__":
    if "--musica" in sys.argv:
        gerar_musica()
    else:
        gerar_efeitos()
    print("OK")
