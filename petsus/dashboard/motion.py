"""Animações decorativas breves, sem representar dados ou mudanças de status."""
from __future__ import annotations


MOTION_CSS = """
@keyframes portal-appear {
    from {opacity:0;transform:translateY(8px);}
    to {opacity:1;transform:translateY(0);}
}
@keyframes portal-line-draw {from {stroke-dashoffset:1;} to {stroke-dashoffset:0;}}
@keyframes portal-bar-rise {from {transform:scaleY(.3);opacity:.35;} to {transform:scaleY(1);opacity:1;}}
@keyframes portal-dot-breathe {0%,100% {opacity:.5;} 50% {opacity:1;}}
@keyframes portal-brand-halo {0%,100% {box-shadow:0 0 0 0 #087F8C00;} 50% {box-shadow:0 0 0 11px #087F8C12;}}
.portal-heading-row {display:flex;align-items:center;justify-content:space-between;gap:1rem;}
.portal-heading-copy {min-width:0;}
.portal-motion-art {display:block;flex:0 0 148px;width:148px;height:78px;color:#087F8C;}
.portal-art-surface {fill:var(--art-surface,#FFFFFFA8);stroke:var(--art-grid,#DCEAF3);}
.portal-art-grid {stroke:var(--art-grid,#DCEAF3);fill:none;}
.portal-art-blue {fill:#287BB5;}
.portal-art-teal {fill:currentColor;}
.portal-art-line {fill:none;stroke:currentColor;stroke-width:2.3;stroke-linecap:round;stroke-linejoin:round;}
.portal-art-line-base {fill:none;stroke:#BBDDDC;stroke-width:2.3;}
.portal-motion-art .portal-art-line {stroke-dasharray:1;animation:portal-line-draw 1.6s .15s ease-out backwards;}
.portal-art-bar {transform-box:fill-box;transform-origin:center bottom;animation:portal-bar-rise .8s ease-out backwards;}
.portal-art-bar:nth-of-type(2) {animation-delay:.12s;}
.portal-art-bar:nth-of-type(3) {animation-delay:.24s;}
.portal-art-dot {animation:portal-dot-breathe 1.4s ease-in-out 2;}
.stApp:has(.patient-portal-marker) .metric-card,
.stApp:has(.patient-portal-marker) .patient-status-card,
.stApp:has(.patient-portal-marker) .patient-next-card {animation:portal-appear .45s ease-out backwards;}
.stApp:has(.patient-portal-marker) [data-testid="stColumn"]:nth-child(2) .metric-card {animation-delay:.05s;}
.stApp:has(.patient-portal-marker) [data-testid="stColumn"]:nth-child(3) .metric-card {animation-delay:.1s;}
.stApp:has(.patient-portal-marker) [data-testid="stColumn"]:nth-child(4) .metric-card {animation-delay:.15s;}
.auth-wrap .auth-brand-symbol {animation:portal-brand-halo 1.6s ease-in-out 2;}
.auth-wrap .auth-brand-name {animation:portal-appear .5s ease-out backwards;}
@container dashboard (max-width:860px) {.portal-motion-art {display:none;}}
@media(max-width:700px) {.portal-motion-art {display:none;}}
@media(prefers-reduced-motion:reduce) {
    .portal-motion-art *,.auth-wrap .auth-brand-symbol,.auth-wrap .auth-brand-name,
    .stApp:has(.patient-portal-marker) .metric-card,
    .stApp:has(.patient-portal-marker) .patient-status-card,
    .stApp:has(.patient-portal-marker) .patient-next-card {animation:none!important;}
}
"""


def header_art(*, contrast: bool = False) -> str:
    contrast_style = ' style="color:#8DE5EF;--art-surface:#000;--art-grid:#64748B"' if contrast else ""
    return (
        f'<svg class="portal-motion-art"{contrast_style} viewBox="0 0 148 78" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">'
        '<rect class="portal-art-surface" x="1" y="1" width="146" height="76" rx="17"/>'
        '<path class="portal-art-grid" d="M15 23h118M15 39h118M15 55h118"/>'
        '<g opacity=".25"><rect class="portal-art-bar portal-art-blue" x="25" y="39" width="13" height="24" rx="4"/>'
        '<rect class="portal-art-bar portal-art-teal" x="47" y="28" width="13" height="35" rx="4"/>'
        '<rect class="portal-art-bar portal-art-blue" x="69" y="16" width="13" height="47" rx="4"/></g>'
        '<path class="portal-art-line-base" d="M16 50h24l12-15 16 10 14-22 14 10h35"/>'
        '<path class="portal-art-line" pathLength="1" d="M16 50h24l12-15 16 10 14-22 14 10h35"/>'
        '<circle class="portal-art-dot portal-art-teal" cx="131" cy="33" r="4"/>'
        '</svg>'
    )
