"""Marcos visuais de acompanhamento individual, sem estimar resultado judicial."""
from html import escape

from petsus.dashboard.patient_ui import icon


TIMELINE_CSS = """
<style>
.care-track {--track-ink:#173653;--track-muted:#536980;--track-line:#DCE6EF;--track-bg:#FFF;--track-soft:#F4F8FC;--track-accent:#087F8C;margin:.6rem 0 1.6rem;color:var(--track-ink);}
.care-track-header {display:flex;align-items:center;gap:.7rem;margin-bottom:.8rem;}
.care-track-header h3 {margin:0!important;padding:0!important;font-size:1.1rem!important;color:inherit!important;}
.care-track-symbol {display:grid;place-items:center;width:42px;height:42px;border-radius:13px;background:var(--track-soft);color:var(--track-accent);flex-shrink:0;}
.care-track-focus {padding:1rem 1.2rem;border:1px solid var(--track-accent);border-left:5px solid var(--track-accent);border-radius:14px;background:var(--track-soft);margin-bottom:1rem;}
.care-track-focus small {display:block;color:var(--track-muted);font-weight:600;margin-bottom:.25rem;}
.care-track-focus strong {font-size:1.05rem;color:var(--track-ink);}
.care-track-steps {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.65rem;list-style:none!important;margin:0!important;padding:0!important;}
.care-track-step {display:flex;align-items:flex-start;gap:.75rem;padding:.85rem;margin:0!important;border:1px solid var(--track-line);border-radius:12px;background:var(--track-bg);min-width:0;}
.care-track-node {display:grid;place-items:center;width:30px;height:30px;flex:0 0 30px;border-radius:50%;border:1px solid var(--track-line);color:var(--track-muted);font-weight:700;font-size:.85rem;}
.care-track-step strong {display:block;font-size:.88rem;line-height:1.5;overflow-wrap:anywhere;color:var(--track-ink);}
.care-track-step small {display:block;font-size:.76rem;color:var(--track-muted);margin-top:.2rem;}
.care-track-step.past .care-track-node {background:var(--track-soft);color:var(--track-accent);}
.care-track-step.current {border:2px solid var(--track-accent);background:var(--track-soft);}
.care-track-step.current .care-track-node {background:var(--track-accent);color:#FFF;border-color:var(--track-accent);}
.care-track-step.current small {font-weight:800;color:var(--track-accent);}
.care-track.contrast {--track-ink:#FFF;--track-muted:#FFF;--track-line:#FFF;--track-bg:#000;--track-soft:#000;--track-accent:#83D6FF;}
.care-track.contrast .care-track-step.current .care-track-node {color:#000;}
@media(max-width:700px) {.care-track-steps {grid-template-columns:minmax(0,1fr);}.care-track-step {padding:.75rem;}}
</style>
"""


def timeline_html(title: str, stages: tuple[str, ...], current: int, status: str, *, health: bool = False, contrast: bool = False) -> str:
    """Render the recorded milestone; zero means the care track has not started."""
    active = current if 1 <= current <= len(stages) else 0
    focus = stages[active - 1] if active else status
    parts = [
        f'<section class="care-track{" contrast" if contrast else ""}" aria-label="{escape(title, quote=True)}">',
        f'<div class="care-track-header"><span class="care-track-symbol">{icon("medical" if health else "scales",24)}</span><h3>{escape(title)}</h3></div>',
        f'<div class="care-track-focus"><small>{"Você está nesta etapa" if active else "Situação do atendimento"}</small><strong>{escape(focus)}</strong></div>',
        '<ol class="care-track-steps">',
    ]
    for index, stage in enumerate(stages, 1):
        state = "current" if index == active else "past" if index < active else "future"
        label = "Etapa atual" if state == "current" else "Etapa anterior" if state == "past" else "Ainda não alcançada"
        marker = icon("check", 17) if state == "past" else str(index)
        aria = ' aria-current="step"' if state == "current" else ""
        parts.append(f'<li class="care-track-step {state}"{aria}><span class="care-track-node" aria-hidden="true">{marker}</span><div><strong>{index}. {escape(stage)}</strong><small>{label}</small></div></li>')
    parts.append('</ol></section>')
    return "".join(parts)
