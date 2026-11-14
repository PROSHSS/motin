"""Estilos de imagem de IA (usado por prompts.py e imagens.py). Troque em config.json: "estilo_imagem"."""
import os

ESTILOS = {
    # fotografia real, documental: o padrao
    "realista": {
        "sufixo": ("Photorealistic candid documentary photograph, shot on a full-frame camera with a 35mm or 50mm lens, natural available light, "
                   "true-to-life colors and materials, realistic textures and small imperfections, subtle film grain, natural depth of field, "
                   "authentic real-world setting, looks like a real press photo. Not an illustration, not CGI, not 3D render, not stock-photo glossy, "
                   "no oversaturation, no text, no watermark."),
        "look": ("The look must be PHOTOREALISTIC and believable, like a real photograph from a documentary or news report: natural light, real textures, "
                 "realistic skin and materials, slightly imperfect framing, natural colors. Never a glossy stock photo, never an illustration or 3D render."),
    },
    # cinema: mais contraste e atmosfera
    "cinematografico": {
        "sufixo": ("Cinematic photorealistic film still, anamorphic 35mm lens, dramatic natural light, rich contrast, soft film grain, realistic textures, "
                   "moody but true-to-life colors, shallow depth of field, looks like a frame from a feature documentary. Not an illustration, not CGI, no text, no watermark."),
        "look": ("The look must be CINEMATIC but PHOTOREALISTIC: dramatic natural light, rich contrast, atmospheric depth, realistic textures, a frame from a feature documentary."),
    },
    # revista/jornal: nitido e limpo
    "editorial": {
        "sufixo": ("Photorealistic editorial photograph for a major magazine, sharp, well exposed, natural colors, realistic textures, professional composition, "
                   "no text, no watermark, not an illustration, not CGI."),
        "look": ("The look must be a PHOTOREALISTIC editorial photograph: sharp, well exposed, natural colors, professional composition."),
    },
    # o visual claro/brilhante de antes
    "limpo": {
        "sufixo": "Bright, clean, sharp professional photograph, well exposed, vivid natural colors, crisp detail, high resolution, no text, no watermark.",
        "look": "The look must be BRIGHT, CLEAN, SHARP and well exposed: no darkness, no murky shadows, no heavy grain, no fog, no vignette.",
    },
}


def estilo():
    return ESTILOS.get(os.environ.get("IMG_ESTILO", "realista"), ESTILOS["realista"])
