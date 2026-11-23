"""Carrossel editorial para Instagram: roteiro em JSON → slides HTML → PNG.

Ideia de arquitetura adaptada do Open Carrusel (MIT), de Enrique Rocha
(@soyenriquerocha) e colaboradores: https://github.com/Hainrixz/open-carrusel
O slide é HTML de corpo, uma única função o embrulha num documento do tamanho
exato do Instagram, e o Chrome sem tela tira a foto. Código reescrito em Python
para a Vista Ideia; ver docs/referencias/open-carrusel/CREDITOS.md.
"""
from .regras import conferir, Problema
from .pagina import FORMATOS, embrulhar, Marca
from .layouts import montar_slide, TIPOS
from .exportar import exportar_carrossel

__all__ = ["conferir", "Problema", "FORMATOS", "embrulhar", "Marca",
           "montar_slide", "TIPOS", "exportar_carrossel"]
