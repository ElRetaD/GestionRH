"""
Fenêtre de connexion — Design Dark Premium Glassmorphism.
Fond noir avec particules flottantes animées, orbes lumineux pulsants,
et carte glassmorphism centrée avec animations dynamiques.
"""
import math
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox, QGraphicsDropShadowEffect,
    QSizePolicy, QApplication
)
from PySide6.QtCore import (
    Qt, Signal, QPropertyAnimation, QPoint, QEasingCurve,
    QTimer, QRectF, QPointF, Property, QParallelAnimationGroup,
    QSequentialAnimationGroup, QSize
)
from PySide6.QtGui import (
    QFont, QColor, QPainter, QLinearGradient, QRadialGradient,
    QBrush, QPen, QPainterPath, QConicalGradient, QPixmap
)
from app.services.auth_service import AuthService


# ══════════════════════════════════════════════════════════════════════════════
#  Particule flottante pour le fond
# ══════════════════════════════════════════════════════════════════════════════

class _Particle:
    """Particule flottante avec mouvement autonome."""
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.radius = random.uniform(1.2, 3.5)
        self.alpha = random.uniform(30, 120)
        self.speed_x = random.uniform(-0.3, 0.3)
        self.speed_y = random.uniform(-0.5, -0.1)
        self.pulse_phase = random.uniform(0, 2 * math.pi)
        self.pulse_speed = random.uniform(0.02, 0.06)
        self.w = w
        self.h = h

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.pulse_phase += self.pulse_speed

        # Wrap around
        if self.y < -10:
            self.y = self.h + 10
            self.x = random.uniform(0, self.w)
        if self.x < -10:
            self.x = self.w + 10
        elif self.x > self.w + 10:
            self.x = -10

    def current_alpha(self):
        return max(10, min(180, self.alpha + 40 * math.sin(self.pulse_phase)))


# ══════════════════════════════════════════════════════════════════════════════
#  Orbe lumineux animé
# ══════════════════════════════════════════════════════════════════════════════

class _GlowOrb:
    """Orbe lumineux flottant avec pulsation et mouvement lent."""
    def __init__(self, cx, cy, rx, ry, color, alpha_base=60):
        self.base_cx = cx
        self.base_cy = cy
        self.rx = rx
        self.ry = ry
        self.color = color
        self.alpha_base = alpha_base
        self.phase = random.uniform(0, 2 * math.pi)
        self.phase_x = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.008, 0.018)
        self.speed_x = random.uniform(0.005, 0.012)
        self.drift_x = random.uniform(15, 40)
        self.drift_y = random.uniform(10, 30)

    def update(self):
        self.phase += self.speed
        self.phase_x += self.speed_x

    def cx(self):
        return self.base_cx + self.drift_x * math.sin(self.phase_x)

    def cy(self):
        return self.base_cy + self.drift_y * math.sin(self.phase)

    def current_alpha(self):
        return max(20, self.alpha_base + 35 * math.sin(self.phase * 1.3))


# ══════════════════════════════════════════════════════════════════════════════
#  Fond animé noir avec particules et orbes
# ══════════════════════════════════════════════════════════════════════════════

class _DarkAnimatedBackground(QWidget):
    """Fond noir premium avec particules flottantes et orbes lumineux."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._particles = []
        self._orbs = []
        self._tick = 0
        self._initialized = False

        # Timer d'animation à ~30 FPS
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(33)

    def _init_elements(self):
        """Initialise particules et orbes selon la taille du widget."""
        w, h = self.width(), self.height()
        if w < 50 or h < 50:
            return

        # Particules
        self._particles = [_Particle(w, h) for _ in range(70)]

        # Orbes lumineux (couleurs sombres avec accent)
        self._orbs = [
            _GlowOrb(w * 0.15, h * 0.20, w * 0.22, h * 0.24,
                      QColor(35, 35, 35), 45),       # Gris sombre subtil
            _GlowOrb(w * 0.85, h * 0.15, w * 0.18, h * 0.20,
                      QColor(45, 45, 45), 40),         # Gris un peu plus clair
            _GlowOrb(w * 0.80, h * 0.78, w * 0.25, h * 0.22,
                      QColor(25, 25, 25), 35),         # Très sombre
            _GlowOrb(w * 0.10, h * 0.75, w * 0.16, h * 0.18,
                      QColor(40, 40, 40), 32),         # Gris intermédiaire
            _GlowOrb(w * 0.50, h * 0.50, w * 0.30, h * 0.28,
                      QColor(20, 20, 20), 25),          # Centre sombre
        ]
        self._initialized = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._init_elements()

    def _animate(self):
        self._tick += 1
        for p in self._particles:
            p.update()
        for orb in self._orbs:
            orb.update()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # ── Fond noir dégradé ────────────────────────────────────────────
        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0.0, QColor(8, 8, 16))
        bg.setColorAt(0.4, QColor(12, 12, 24))
        bg.setColorAt(0.7, QColor(10, 10, 20))
        bg.setColorAt(1.0, QColor(6, 6, 14))
        p.fillRect(0, 0, w, h, QBrush(bg))

        if not self._initialized:
            p.end()
            return

        # ── Grille subtile ───────────────────────────────────────────────
        grid_pen = QPen(QColor(255, 255, 255, 6))
        grid_pen.setWidthF(0.5)
        p.setPen(grid_pen)
        spacing = 60
        for x in range(0, w + 1, spacing):
            p.drawLine(x, 0, x, h)
        for y in range(0, h + 1, spacing):
            p.drawLine(0, y, w, y)

        # ── Orbes lumineux ───────────────────────────────────────────────
        for orb in self._orbs:
            grad = QRadialGradient(orb.cx(), orb.cy(), max(orb.rx, orb.ry))
            c = QColor(orb.color)
            alpha = int(orb.current_alpha())
            c.setAlpha(alpha)
            c2 = QColor(orb.color)
            c2.setAlpha(max(0, alpha // 3))
            c3 = QColor(orb.color)
            c3.setAlpha(0)

            grad.setColorAt(0.0, c)
            grad.setColorAt(0.4, c2)
            grad.setColorAt(1.0, c3)

            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(grad))
            p.drawEllipse(
                QRectF(orb.cx() - orb.rx, orb.cy() - orb.ry,
                       orb.rx * 2, orb.ry * 2)
            )

        # ── Particules ───────────────────────────────────────────────────
        for particle in self._particles:
            alpha = int(particle.current_alpha())
            color = QColor(255, 255, 255, alpha)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(color))
            p.drawEllipse(
                QPointF(particle.x, particle.y),
                particle.radius, particle.radius
            )

        # ── Lignes de connexion entre particules proches ─────────────────
        for i, p1 in enumerate(self._particles):
            for p2 in self._particles[i+1:]:
                dx = p1.x - p2.x
                dy = p1.y - p2.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 120:
                    alpha = int(max(0, 25 * (1 - dist / 120)))
                    line_pen = QPen(QColor(255, 255, 255, alpha))
                    line_pen.setWidthF(0.5)
                    p.setPen(line_pen)
                    p.drawLine(QPointF(p1.x, p1.y), QPointF(p2.x, p2.y))

        p.end()


# ══════════════════════════════════════════════════════════════════════════════
#  Bouton animé avec glow dynamique
# ══════════════════════════════════════════════════════════════════════════════

class _GlowButton(QPushButton):
    """Bouton premium avec effet glow animé au survol."""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._glow_intensity = 0
        self._hover = False
        self.setFixedHeight(50)
        self.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.setCursor(Qt.PointingHandCursor)

        # Animation du glow
        self._glow_anim = QPropertyAnimation(self, b"glowIntensity")
        self._glow_anim.setDuration(300)
        self._glow_anim.setEasingCurve(QEasingCurve.OutCubic)

    def _get_glow_intensity(self):
        return self._glow_intensity

    def _set_glow_intensity(self, val):
        self._glow_intensity = val
        self.update()
        # Update shadow dynamically
        s = QGraphicsDropShadowEffect(self)
        s.setBlurRadius(20 + val * 30)
        s.setOffset(0, 4 + val * 4)
        c = QColor(100, 140, 255)
        c.setAlpha(int(40 + val * 100))
        s.setColor(c)
        self.setGraphicsEffect(s)

    glowIntensity = Property(float, _get_glow_intensity, _set_glow_intensity)

    def enterEvent(self, event):
        self._hover = True
        self._glow_anim.stop()
        self._glow_anim.setStartValue(self._glow_intensity)
        self._glow_anim.setEndValue(1.0)
        self._glow_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._glow_anim.stop()
        self._glow_anim.setStartValue(self._glow_intensity)
        self._glow_anim.setEndValue(0.0)
        self._glow_anim.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        gi = self._glow_intensity

        # Background gradient
        rect = QRectF(0, 0, w, h)
        path = QPainterPath()
        path.addRoundedRect(rect, 14, 14)

        grad = QLinearGradient(0, 0, w, 0)
        if self.isEnabled():
            # Interpoler entre normal et hover
            r1 = int(18 + gi * 20)
            g1 = int(22 + gi * 30)
            b1 = int(50 + gi * 60)
            r2 = int(30 + gi * 35)
            g2 = int(35 + gi * 50)
            b2 = int(80 + gi * 80)
            grad.setColorAt(0.0, QColor(r1, g1, b1))
            grad.setColorAt(0.5, QColor(r2, g2, b2))
            grad.setColorAt(1.0, QColor(r1, g1, b1))
        else:
            grad.setColorAt(0.0, QColor(30, 30, 40))
            grad.setColorAt(1.0, QColor(25, 25, 35))

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(grad))
        p.drawPath(path)

        # Border glow
        if gi > 0.01:
            border_pen = QPen(QColor(100, 140, 255, int(gi * 120)))
            border_pen.setWidthF(1.5)
            p.setPen(border_pen)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(0.75, 0.75, w - 1.5, h - 1.5), 14, 14)

        # Shimmer line on hover
        if gi > 0.3:
            shimmer_x = (self._glow_intensity * w * 1.5) % (w + 60) - 30
            shimmer = QLinearGradient(shimmer_x - 30, 0, shimmer_x + 30, 0)
            shimmer.setColorAt(0.0, QColor(255, 255, 255, 0))
            shimmer.setColorAt(0.5, QColor(255, 255, 255, int(gi * 25)))
            shimmer.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(shimmer))
            p.drawPath(path)

        # Text
        if self.isEnabled():
            text_color = QColor(255, 255, 255, int(200 + gi * 55))
        else:
            text_color = QColor(255, 255, 255, 90)
        p.setPen(text_color)
        p.setFont(self.font())
        p.drawText(rect, Qt.AlignCenter, self.text())

        p.end()


# ══════════════════════════════════════════════════════════════════════════════
#  Fenêtre principale Login
# ══════════════════════════════════════════════════════════════════════════════

class LoginWindow(QWidget):
    """Fenêtre de connexion — Dark Premium Glassmorphism Style."""

    login_success = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GestRH — Connexion")
        self.setMinimumSize(800, 600)
        self.resize(1100, 750)

        # Fond animé
        self._bg = _DarkAnimatedBackground(self)
        self._bg.lower()

        self._build_ui()

        # Animation d'entrée de la carte
        QTimer.singleShot(100, self._animate_card_entrance)

    def resizeEvent(self, event):
        self._bg.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    # ─── Shadow ───────────────────────────────────────────────────────────────

    def _shadow(self, widget, color="#000000", blur=48, alpha=120, oy=20):
        s = QGraphicsDropShadowEffect(widget)
        s.setBlurRadius(blur)
        s.setOffset(0, oy)
        c = QColor(color)
        c.setAlpha(alpha)
        s.setColor(c)
        widget.setGraphicsEffect(s)

    # ─── Card entrance animation ──────────────────────────────────────────────

    def _animate_card_entrance(self):
        """Fait apparaître la carte avec un effet slide-up + fade."""
        self.auth_card.setVisible(True)
        anim = QPropertyAnimation(self.auth_card, b"pos")
        anim.setDuration(700)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        target_pos = self.auth_card.pos()
        start_pos = target_pos + QPoint(0, 60)
        anim.setStartValue(start_pos)
        anim.setEndValue(target_pos)
        anim.start()
        self._entrance_anim = anim

    # ─── Main UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setAlignment(Qt.AlignCenter)

        # Carte glassmorphism centrée
        self.auth_card = QFrame()
        self.auth_card.setObjectName("authCard")
        self.auth_card.setFixedWidth(420)
        self.auth_card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.auth_card.setStyleSheet("""
            QFrame#authCard {
                background: rgba(18, 18, 28, 0.75);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 28px;
            }
            QFrame#authCard QLabel {
                background: transparent;
                border: none;
                border-radius: 0px;
            }
            QFrame#authCard QCheckBox {
                background: transparent;
                border: none;
            }
            QFrame#authCard QFrame {
                background: transparent;
                border: none;
                border-radius: 0px;
            }
        """)
        self._shadow(self.auth_card, "#000000", blur=80, alpha=160, oy=30)

        cl = QVBoxLayout(self.auth_card)
        cl.setContentsMargins(44, 40, 44, 40)
        cl.setSpacing(0)

        # ── Logo ──────────────────────────────────────────────────────────
        logo_row = QHBoxLayout()
        logo_row.setAlignment(Qt.AlignCenter)

        import os
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "assets", "logo.png"
        )
        
        # Container avec border radius
        logo_bg = QLabel()
        logo_bg.setFixedSize(64, 64)
        logo_bg.setAlignment(Qt.AlignCenter)
        logo_bg.setStyleSheet("""
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 18px;
        """)

        # Label interne pour l'image
        logo_inner = QLabel(logo_bg)
        logo_inner.setFixedSize(48, 48)
        logo_inner.setGeometry(8, 8, 48, 48)
        logo_inner.setAlignment(Qt.AlignCenter)
        logo_inner.setStyleSheet("background: transparent; border: none;")

        if os.path.exists(logo_path):
            original_pixmap = QPixmap(logo_path)
            # Créer un pixmap arrondi pour l'insérer proprement
            rounded_pixmap = QPixmap(48, 48)
            rounded_pixmap.fill(Qt.transparent)
            
            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            path = QPainterPath()
            path.addRoundedRect(0, 0, 48, 48, 12, 12)
            painter.setClipPath(path)
            
            painter.drawPixmap(0, 0, original_pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            painter.end()
            
            logo_inner.setPixmap(rounded_pixmap)
        else:
            logo_inner.setText("S")
            logo_inner.setFont(QFont("Segoe UI", 24, QFont.Bold))
            logo_inner.setStyleSheet("color: white;")
            
        logo_row.addWidget(logo_bg)
        cl.addLayout(logo_row)
        cl.addSpacing(14)

        # App name
        app_name = QLabel("GestRH")
        app_name.setAlignment(Qt.AlignCenter)
        app_name.setFont(QFont("Segoe UI", 15, QFont.Bold))
        app_name.setStyleSheet(
            "color: rgba(255,255,255,0.90); background: transparent; "
            "letter-spacing: 1px;"
        )
        cl.addWidget(app_name)
        cl.addSpacing(28)

        # ── Title ─────────────────────────────────────────────────────────
        title = QLabel("Connexion")
        title.setFont(QFont("Segoe UI", 24, QFont.Black))
        title.setStyleSheet("color: white; background: transparent;")
        cl.addWidget(title)
        cl.addSpacing(6)

        sub = QLabel("Identifiez-vous pour accéder à votre espace.")
        sub.setWordWrap(True)
        sub.setStyleSheet(
            "color: rgba(255,255,255,0.45); font-size: 12px; background: transparent;"
        )
        cl.addWidget(sub)
        cl.addSpacing(28)

        # ── Username ──────────────────────────────────────────────────────
        cl.addWidget(self._field_label("Nom d'utilisateur"))
        cl.addSpacing(7)
        self.username_input = self._input("Votre identifiant...")
        self.username_input.returnPressed.connect(self._do_login)
        cl.addWidget(self.username_input)
        cl.addSpacing(18)

        # ── Password ──────────────────────────────────────────────────────
        cl.addWidget(self._field_label("Mot de passe"))
        cl.addSpacing(7)
        self.password_input = self._input("••••••••")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self._do_login)
        cl.addWidget(self.password_input)
        cl.addSpacing(10)

        # ── Show password ─────────────────────────────────────────────────
        show_pwd = QCheckBox("Afficher le mot de passe")
        show_pwd.setStyleSheet("""
            QCheckBox {
                color: rgba(255,255,255,0.50);
                font-size: 12px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border-radius: 5px;
                border: 1.5px solid rgba(255,255,255,0.20);
                background: rgba(255,255,255,0.05);
            }
            QCheckBox::indicator:checked {
                background: rgba(100,140,255,0.60);
                border-color: rgba(100,140,255,0.80);
                image: none;
            }
        """)
        show_pwd.toggled.connect(
            lambda ok: self.password_input.setEchoMode(
                QLineEdit.Normal if ok else QLineEdit.Password
            )
        )
        cl.addWidget(show_pwd)
        cl.addSpacing(10)

        # ── Error label ───────────────────────────────────────────────────
        self.error_lbl = QLabel("")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setStyleSheet("""
            color: #FF90A0;
            background: rgba(255, 40, 60, 0.12);
            border: 1px solid rgba(255, 80, 100, 0.25);
            border-radius: 12px;
            padding: 10px 14px;
            font-size: 12px;
            font-weight: 600;
        """)
        self.error_lbl.hide()
        cl.addWidget(self.error_lbl)

        # ── Login button (animated glow) ─────────────────────────────────
        cl.addSpacing(6)
        self.login_btn = _GlowButton("Se Connecter")
        self.login_btn.clicked.connect(self._do_login)
        cl.addWidget(self.login_btn)
        cl.addSpacing(22)

        # ── Separator ──────────────────────────────────────────────────
        sep_lbl = QLabel()
        sep_lbl.setFixedHeight(1)
        sep_lbl.setStyleSheet(
            "background: rgba(255,255,255,0.08); border: none;"
        )
        cl.addWidget(sep_lbl)
        cl.addSpacing(14)

        # ── Credentials hint ──────────────────────────────────────────────
        creds = QLabel(
            "🏢  SBZS  ·  Portail de Gestion des Ressources Humaines"
        )
        creds.setAlignment(Qt.AlignCenter)
        creds.setWordWrap(True)
        creds.setStyleSheet(
            "color: rgba(255,255,255,0.30); font-size: 11px; background: transparent; font-weight: 500;"
        )
        cl.addWidget(creds)

        root.addWidget(self.auth_card, 0, Qt.AlignCenter)
        self.username_input.setFocus()

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color: rgba(255,255,255,0.60); font-weight: 700; "
            "font-size: 12px; background: transparent; letter-spacing: 0.3px;"
        )
        return lbl

    def _input(self, placeholder: str) -> QLineEdit:
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(46)
        inp.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.06);
                border: 1.5px solid rgba(255,255,255,0.10);
                border-radius: 12px;
                padding: 0 16px;
                color: rgba(255,255,255,0.90);
                font-size: 13px;
                font-weight: 500;
                selection-background-color: rgba(100,140,255,0.40);
            }
            QLineEdit:focus {
                background: rgba(255, 255, 255, 0.09);
                border-color: rgba(100,140,255,0.50);
            }
            QLineEdit::placeholder {
                color: rgba(255,255,255,0.25);
            }
        """)
        return inp

    # ─── Logic ────────────────────────────────────────────────────────────────

    def _do_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self._show_error("⚠  Veuillez remplir tous les champs.")
            return

        self.login_btn.setText("Connexion en cours...")
        self.login_btn.setEnabled(False)

        user = AuthService.login(username, password)

        if user:
            self.error_lbl.hide()
            self.login_success.emit(user)
        else:
            self.login_btn.setText("Se Connecter")
            self.login_btn.setEnabled(True)
            self._show_error("❌  Identifiant ou mot de passe incorrect.")
            self._shake()
            self.password_input.clear()

    def _show_error(self, msg: str):
        self.error_lbl.setText(msg)
        self.error_lbl.show()

    def _shake(self):
        anim = QPropertyAnimation(self.auth_card, b"pos")
        anim.setDuration(460)
        anim.setEasingCurve(QEasingCurve.OutElastic)
        pos = self.auth_card.pos()
        anim.setKeyValueAt(0.0,  pos)
        anim.setKeyValueAt(0.12, pos + QPoint(-14, 0))
        anim.setKeyValueAt(0.30, pos + QPoint(14, 0))
        anim.setKeyValueAt(0.50, pos + QPoint(-9, 0))
        anim.setKeyValueAt(0.70, pos + QPoint(9, 0))
        anim.setKeyValueAt(0.86, pos + QPoint(-4, 0))
        anim.setKeyValueAt(1.0,  pos)
        anim.start()
        self._shake_ref = anim
