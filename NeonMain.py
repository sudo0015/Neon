# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import requests
import NeonResource
from typing import Union
from NeonConfig import cfg
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize, pyqtProperty, QRect, QRectF, QEvent, QUrl, QThread, QDate, \
    QTimer, QEasingCurve
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QIcon, QDesktopServices, QFontMetrics, QFont, \
    QImage, QPixmap, QImageReader, QMovie
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QStackedWidget, QWidget, QGridLayout, QListWidget, \
    QListWidgetItem, QFrame, QSwipeGesture, QPushButton, QSizePolicy, QStyleOptionButton, QStyle, QLabel, QScrollArea, \
    QScroller, QSystemTrayIcon, QAction
from PyQt5.QtSvg import QSvgRenderer
from qfluentwidgets import FluentIcon, isDarkTheme, HorizontalPipsPager, drawIcon, PipsScrollButtonDisplayMode, \
    SmoothScrollBar, FluentStyleSheet, ToolTipFilter, ToolTipPosition, Theme, setFont, FluentIconBase, themeColor, \
    qconfig, setCustomStyleSheet, getFont, SmoothScrollDelegate, FluentFontIconBase
from qfluentwidgets.components.widgets.menu import LabelContextMenu, RoundMenu
from qfluentwidgets.common.animation import BackgroundAnimationWidget
from qfluentwidgets.components.widgets.pips_pager import PipsDelegate, ScrollButton
from qfluentwidgets.common.overload import singledispatchmethod


class FluentFontIcon(FluentFontIconBase):

    def path(self, theme=Theme.AUTO):
        return "Font/SegoeIcons.ttf"


class PipsPager(QListWidget):
    """
    Pips pager

    Constructors
    ------------
    * PipsPager(`parent`: QWidget = None)
    * PipsPager(`orient`: Qt.Orientation, `parent`: QWidget = None)
    """

    currentIndexChanged = pyqtSignal(int)

    @singledispatchmethod
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.orientation = Qt.Horizontal
        self._postInit()

    @__init__.register
    def _(self, orientation: Qt.Orientation, parent=None):
        super().__init__(parent=parent)
        self.orientation = orientation
        self._postInit()

    def _postInit(self):
        self._visibleNumber = 5
        self.isHover = False

        self.delegate = PipsDelegate(self)
        self.scrollBar = SmoothScrollBar(self.orientation, self)

        self.scrollBar.setScrollAnimation(500)
        self.scrollBar.setForceHidden(True)

        self.setMouseTracking(True)
        self.setUniformItemSizes(True)
        self.setGridSize(QSize(12, 12))
        self.setItemDelegate(self.delegate)
        self.setMovement(QListWidget.Static)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        FluentStyleSheet.PIPS_PAGER.apply(self)

        if self.isHorizontal():
            self.setFlow(QListWidget.LeftToRight)
            self.setViewportMargins(15, 0, 15, 0)
            self.preButton = ScrollButton(FluentIcon.CARE_LEFT_SOLID, self)
            self.nextButton = ScrollButton(FluentIcon.CARE_RIGHT_SOLID, self)
            self.setFixedHeight(12)

            self.preButton.installEventFilter(ToolTipFilter(self.preButton, 1000, ToolTipPosition.LEFT))
            self.nextButton.installEventFilter(ToolTipFilter(self.nextButton, 1000, ToolTipPosition.RIGHT))

        else:
            self.setViewportMargins(0, 15, 0, 15)
            self.preButton = ScrollButton(FluentIcon.CARE_UP_SOLID, self)
            self.nextButton = ScrollButton(FluentIcon.CARE_DOWN_SOLID, self)
            self.setFixedWidth(12)

            self.preButton.installEventFilter(ToolTipFilter(self.preButton, 1000, ToolTipPosition.TOP))
            self.nextButton.installEventFilter(ToolTipFilter(self.nextButton, 1000, ToolTipPosition.BOTTOM))

        self.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.NEVER)
        self.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.NEVER)
        self.preButton.setToolTip("上一个组件")
        self.nextButton.setToolTip("下一个组件")

        self.preButton.clicked.connect(self.scrollPrevious)
        self.nextButton.clicked.connect(self.scrollNext)
        self.itemPressed.connect(self._setPressedItem)
        self.itemEntered.connect(self._setHoveredItem)

    def _setPressedItem(self, item: QListWidgetItem):
        self.delegate.setPressedRow(self.row(item))
        self.setCurrentIndex(self.row(item))

    def _setHoveredItem(self, item: QListWidgetItem):
        self.delegate.setHoveredRow(self.row(item))

    def setPageNumber(self, n: int):
        """ set the number of page """
        self.clear()
        self.addItems(['15555'] * n)

        for i in range(n):
            item = self.item(i)
            item.setData(Qt.UserRole, i + 1)
            item.setSizeHint(self.gridSize())

        self.setCurrentIndex(0)
        self.adjustSize()

    def getPageNumber(self):
        """ get the number of page """
        return self.count()

    def getVisibleNumber(self):
        """ get the number of visible pips """
        return self._visibleNumber

    def setVisibleNumber(self, n: int):
        self._visibleNumber = n
        self.adjustSize()

    def scrollNext(self):
        """ scroll down an item """
        self.setCurrentIndex(self.currentIndex() + 1)

    def scrollPrevious(self):
        """ scroll up an item """
        self.setCurrentIndex(self.currentIndex() - 1)

    def scrollToItem(self, item: QListWidgetItem, hint=QListWidget.PositionAtCenter):
        """ scroll to item """
        index = self.row(item)
        size = item.sizeHint()
        s = size.width() if self.isHorizontal() else size.height()
        self.scrollBar.scrollTo(s * (index - self.visibleNumber // 2))

        self.clearSelection()
        item.setSelected(False)

        self.currentIndexChanged.emit(index)

    def adjustSize(self) -> None:
        m = self.viewportMargins()

        if self.isHorizontal():
            w = self.visibleNumber * self.gridSize().width() + m.left() + m.right()
            self.setFixedWidth(w)
        else:
            h = self.visibleNumber * self.gridSize().height() + m.top() + m.bottom()
            self.setFixedHeight(h)

    def isHorizontal(self):
        return self.orientation == Qt.Horizontal

    def setCurrentIndex(self, index: int):
        """ set current index """
        if not 0 <= index < self.count():
            return

        item = self.item(index)
        self.scrollToItem(item)
        super().setCurrentItem(item)

        self._updateScrollButtonVisibility()

    def isPreviousButtonVisible(self):
        if self.currentIndex() <= 0 or self.previousButtonDisplayMode == PipsScrollButtonDisplayMode.NEVER:
            return False

        if self.previousButtonDisplayMode == PipsScrollButtonDisplayMode.ON_HOVER:
            return self.isHover

        return True

    def isNextButtonVisible(self):
        if self.currentIndex() >= self.count() - 1 or self.nextButtonDisplayMode == PipsScrollButtonDisplayMode.NEVER:
            return False

        if self.nextButtonDisplayMode == PipsScrollButtonDisplayMode.ON_HOVER:
            return self.isHover

        return True

    def currentIndex(self):
        return super().currentIndex().row()

    def setPreviousButtonDisplayMode(self, mode: PipsScrollButtonDisplayMode):
        """ set the display mode of previous button """
        self.previousButtonDisplayMode = mode
        self.preButton.setVisible(self.isPreviousButtonVisible())

    def setNextButtonDisplayMode(self, mode: PipsScrollButtonDisplayMode):
        """ set the display mode of next button """
        self.nextButtonDisplayMode = mode
        self.nextButton.setVisible(self.isNextButtonVisible())

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.delegate.setPressedRow(-1)

    def enterEvent(self, e):
        super().enterEvent(e)
        self.isHover = True
        self._updateScrollButtonVisibility()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self.isHover = False
        self.delegate.setHoveredRow(-1)
        self._updateScrollButtonVisibility()

    def _updateScrollButtonVisibility(self):
        self.preButton.setVisible(self.isPreviousButtonVisible())
        self.nextButton.setVisible(self.isNextButtonVisible())

    def wheelEvent(self, e):
        pass

    def resizeEvent(self, e):
        w, h = self.width(), self.height()
        bw, bh = self.preButton.width(), self.preButton.height()

        if self.isHorizontal():
            self.preButton.move(0, int(h / 2 - bh / 2))
            self.nextButton.move(w - bw, int(h / 2 - bh / 2))
        else:
            self.preButton.move(int(w / 2 - bw / 2), 0)
            self.nextButton.move(int(w / 2 - bw / 2), h - bh)

    visibleNumber = pyqtProperty(int, getVisibleNumber, setVisibleNumber)
    pageNumber = pyqtProperty(int, getPageNumber, setPageNumber)


class HorizontalPipsPager(PipsPager):
    """ Horizontal pips pager """

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)


class SmoothScrollArea(QScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewport().setAttribute(Qt.WA_AcceptTouchEvents, True)
        self.delegate = SmoothScrollDelegate(self, True)
        QScroller.grabGesture(self.viewport(), QScroller.TouchGesture)

    def setScrollAnimation(self, orient, duration, easing=QEasingCurve.OutCubic):
        """ set scroll animation

        Parameters
        ----------
        orient: Orient
            scroll orientation

        duration: int
            scroll duration

        easing: QEasingCurve
            animation type
        """
        bar = self.delegate.hScrollBar if orient == Qt.Horizontal else self.delegate.vScrollBar
        bar.setScrollAnimation(duration, easing)

    def enableTransparentBackground(self):
        self.setStyleSheet("QScrollArea{border: none; background: transparent}")

        if self.widget():
            self.widget().setStyleSheet("QWidget{background: transparent}")


class FluentLabelBase(QLabel):
    """ Fluent label base class

    Constructors
    ------------
    * FluentLabelBase(`parent`: QWidget = None)
    * FluentLabelBase(`text`: str, `parent`: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._init()

    @__init__.register
    def _(self, text: str, parent: QWidget = None):
        self.__init__(parent)
        self.setText(text)

    def _init(self):
        FluentStyleSheet.LABEL.apply(self)
        self.setFont(self.getFont())
        self.setTextColor()
        connect = qconfig.themeChanged.connect(lambda: self.setTextColor(self.lightColor, self.darkColor))
        self.destroyed.connect(lambda: self.disconnect(connect))

        self.customContextMenuRequested.connect(self._onContextMenuRequested)
        return self

    def getFont(self):
        raise NotImplementedError

    def setTextColor(self, light=QColor(0, 0, 0), dark=QColor(255, 255, 255)):
        """ set the text color of label

        Parameters
        ----------
        light, dark: QColor | Qt.GlobalColor | str
            text color in light/dark mode
        """
        self._lightColor = QColor(light)
        self._darkColor = QColor(dark)

        setCustomStyleSheet(
            self,
            f"FluentLabelBase{{color:{self.lightColor.name(QColor.NameFormat.HexArgb)}}}",
            f"FluentLabelBase{{color:{self.darkColor.name(QColor.NameFormat.HexArgb)}}}"
        )

    @pyqtProperty(QColor)
    def lightColor(self):
        return self._lightColor

    @lightColor.setter
    def lightColor(self, color: QColor):
        self.setTextColor(color, self.darkColor)

    @pyqtProperty(QColor)
    def darkColor(self):
        return self._darkColor

    @darkColor.setter
    def darkColor(self, color: QColor):
        self.setTextColor(self.lightColor, color)

    @pyqtProperty(int)
    def pixelFontSize(self):
        return self.font().pixelSize()

    @pixelFontSize.setter
    def pixelFontSize(self, size: int):
        font = self.font()
        font.setPixelSize(size)
        self.setFont(font)

    @pyqtProperty(bool)
    def strikeOut(self):
        return self.font().strikeOut()

    @strikeOut.setter
    def strikeOut(self, isStrikeOut: bool):
        font = self.font()
        font.setStrikeOut(isStrikeOut)
        self.setFont(font)

    @pyqtProperty(bool)
    def underline(self):
        return self.font().underline()

    @underline.setter
    def underline(self, isUnderline: bool):
        font = self.font()
        font.setStyle()
        font.setUnderline(isUnderline)
        self.setFont(font)

    def _onContextMenuRequested(self, pos):
        menu = LabelContextMenu(parent=self)
        menu.exec(self.mapToGlobal(pos))


class WeatherTitleLabel(FluentLabelBase):
    def getFont(self):
        return getFont(32, QFont.Bold)


class WeatherContentLabel(FluentLabelBase):
    def getFont(self):
        return getFont(16, QFont.DemiBold)


class MottoLabel(FluentLabelBase):
    def getFont(self):
        return getFont(18, QFont.Bold)


class CountdownEventLabel(FluentLabelBase):
    def getFont(self):
        return getFont(28, QFont.Bold)


class CountdownDisplayLabel(FluentLabelBase):
    def getFont(self):
        return getFont(72, QFont.Bold)


class ImageLabel(QLabel):
    """ Image label

    Constructors
    ------------
    * ImageLabel(`parent`: QWidget = None)
    * ImageLabel(`image`: str | QImage | QPixmap, `parent`: QWidget = None)
    """

    clicked = pyqtSignal()

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.image = QImage()
        self.svgRenderer = None
        self.setBorderRadius(0, 0, 0, 0)
        self._postInit()

    @__init__.register
    def _(self, image: str, parent=None):
        self.__init__(parent)
        self.setImage(image)

    @__init__.register
    def _(self, image: QImage, parent=None):
        self.__init__(parent)
        self.setImage(image)

    @__init__.register
    def _(self, image: QPixmap, parent=None):
        self.__init__(parent)
        self.setImage(image)

    def _postInit(self):
        pass

    def _onFrameChanged(self, index: int):
        self.image = self.movie().currentImage()
        self.update()

    def setBorderRadius(self, topLeft: int, topRight: int, bottomLeft: int, bottomRight: int):
        """ set the border radius of image """
        self._topLeftRadius = topLeft
        self._topRightRadius = topRight
        self._bottomLeftRadius = bottomLeft
        self._bottomRightRadius = bottomRight
        self.update()

    def setImage(self, image: Union[str, QPixmap, QImage] = None):
        """ set the image of label """
        self.svgRenderer = None

        if isinstance(image, str):
            if image.lower().endswith('.svg'):
                self.svgRenderer = QSvgRenderer(image)
                if self.svgRenderer.isValid():
                    default_size = self.svgRenderer.defaultSize()
                    if not default_size.isValid():
                        default_size = QSize(100, 100)
                    self.setFixedSize(default_size)
                else:
                    reader = QImageReader(image)
                    if reader.supportsAnimation():
                        self.setMovie(QMovie(image))
                    else:
                        self.image = reader.read()
            else:
                reader = QImageReader(image)
                if reader.supportsAnimation():
                    self.setMovie(QMovie(image))
                else:
                    self.image = reader.read()
                    self.setFixedSize(self.image.size())
        elif isinstance(image, QPixmap):
            self.image = image.toImage()
            self.setFixedSize(self.image.size())
        elif isinstance(image, QImage):
            self.image = image
            self.setFixedSize(self.image.size())
        else:
            self.image = QImage()

        self.update()

    def scaledToWidth(self, width: int):
        if self.isNull():
            return

        if self.svgRenderer:
            default_size = self.svgRenderer.defaultSize()
            if default_size.isValid() and default_size.width() > 0:
                h = int(width * default_size.height() / default_size.width())
                self.setFixedSize(width, h)
            else:
                self.setFixedSize(width, width)
        else:
            h = int(width / self.image.width() * self.image.height())
            self.setFixedSize(width, h)

            if self.movie():
                self.movie().setScaledSize(QSize(width, h))

    def scaledToHeight(self, height: int):
        if self.isNull():
            return

        if self.svgRenderer:
            default_size = self.svgRenderer.defaultSize()
            if default_size.isValid() and default_size.height() > 0:
                w = int(height * default_size.width() / default_size.height())
                self.setFixedSize(w, height)
            else:
                self.setFixedSize(height, height)
        else:
            w = int(height / self.image.height() * self.image.width())
            self.setFixedSize(w, height)

            if self.movie():
                self.movie().setScaledSize(QSize(w, height))

    def setScaledSize(self, size: QSize):
        if self.isNull():
            return

        self.setFixedSize(size)

        if self.movie():
            self.movie().setScaledSize(size)

    def isNull(self):
        return not self.svgRenderer and self.image.isNull()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.clicked.emit()

    def setPixmap(self, pixmap: QPixmap):
        self.setImage(pixmap)

    def pixmap(self) -> QPixmap:
        if self.svgRenderer:
            pixmap = QPixmap(self.size())
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            self.svgRenderer.render(painter, QRectF(pixmap.rect()))
            painter.end()
            return pixmap
        return QPixmap.fromImage(self.image)

    def setMovie(self, movie: QMovie):
        super().setMovie(movie)
        self.movie().start()
        self.image = self.movie().currentImage()
        self.movie().frameChanged.connect(self._onFrameChanged)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        path = QPainterPath()
        w, h = self.width(), self.height()
        path.moveTo(self._topLeftRadius, 0)
        path.lineTo(w - self._topRightRadius, 0)
        d = self._topRightRadius * 2
        path.arcTo(w - d, 0, d, d, 90, -90)
        path.lineTo(w, h - self._bottomRightRadius)
        d = self._bottomRightRadius * 2
        path.arcTo(w - d, h - d, d, d, 0, -90)
        path.lineTo(self._bottomLeftRadius, h)
        d = self._bottomLeftRadius * 2
        path.arcTo(0, h - d, d, d, -90, -90)
        path.lineTo(0, self._topLeftRadius)
        d = self._topLeftRadius * 2
        path.arcTo(0, 0, d, d, -180, -90)
        painter.setPen(Qt.NoPen)
        painter.setClipPath(path)

        if self.svgRenderer and self.svgRenderer.isValid():
            self.svgRenderer.render(painter, QRectF(0, 0, w, h))
        elif not self.image.isNull():
            image = self.image.scaled(
                self.size() * self.devicePixelRatioF(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            image.setDevicePixelRatio(self.devicePixelRatioF())
            painter.drawImage(self.rect(), image)

    @pyqtProperty(int)
    def topLeftRadius(self):
        return self._topLeftRadius

    @topLeftRadius.setter
    def topLeftRadius(self, radius: int):
        self.setBorderRadius(radius, self.topRightRadius, self.bottomLeftRadius, self.bottomRightRadius)

    @pyqtProperty(int)
    def topRightRadius(self):
        return self._topRightRadius

    @topRightRadius.setter
    def topRightRadius(self, radius: int):
        self.setBorderRadius(self.topLeftRadius, radius, self.bottomLeftRadius, self.bottomRightRadius)

    @pyqtProperty(int)
    def bottomLeftRadius(self):
        return self._bottomLeftRadius

    @bottomLeftRadius.setter
    def bottomLeftRadius(self, radius: int):
        self.setBorderRadius(self.topLeftRadius, self.topRightRadius, radius, self.bottomRightRadius)

    @pyqtProperty(int)
    def bottomRightRadius(self):
        return self._bottomRightRadius

    @bottomRightRadius.setter
    def bottomRightRadius(self, radius: int):
        self.setBorderRadius(
            self.topLeftRadius, self.topRightRadius, self.bottomLeftRadius, radius)


class CurriculumButton(QPushButton):
    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._url = QUrl()
        self._large_text = ""
        self._small_text = ""
        self._large_size = cfg.FontSizeBig.value
        self._small_size = cfg.FontSizeSmall.value
        self._spacing = 0
        self._custom_color = None

        self.setStyleSheet(
            "QPushButton {font: '" + cfg.FontFamily.value + "'; padding: 6px 12px 6px 12px; color: rgb(0, 159, 170); border: none; border-radius: 6px; background-color: transparent;}"
            "QPushButton:hover {color: rgb(0, 159, 170); background-color: rgba(0, 0, 0, 10); border: none;}"
            "QPushButton:pressed {color: rgb(0, 159, 170); background-color: rgba(0, 0, 0, 6); border: none;}"
            "QPushButton:disabled {color: rgba(0, 0, 0, 0.43); background-color: transparent; border: none;}"
        )
        self.setCursor(Qt.PointingHandCursor)
        setFont(self)
        self.clicked.connect(self._onClicked)

    @__init__.register
    def _(self, url: str, text: str, parent: QWidget = None, icon: Union[QIcon, FluentIconBase, str] = None):
        self.__init__(parent)
        self.setText(text)
        self.url.setUrl(url)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, url: str, text: str, parent: QWidget = None):
        self.__init__(url, text, parent, icon)

    @__init__.register
    def _(self, icon: FluentIconBase, url: str, text: str, parent: QWidget = None):
        self.__init__(url, text, parent, icon)

    def getUrl(self):
        return self._url

    def setUrl(self, url: Union[str, QUrl]):
        self._url = QUrl(url)

    def _onClicked(self):
        url = self.getUrl()
        if url.isValid():
            if url.scheme() == 'file':
                local_path = url.toLocalFile()
                if os.path.exists(local_path):
                    QDesktopServices.openUrl(url)
            else:
                QDesktopServices.openUrl(url)

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        if isinstance(icon, FluentIconBase) and self.isEnabled():
            icon = icon.icon(color=themeColor())
        elif not self.isEnabled():
            painter.setOpacity(0.3628 if isDarkTheme() else 0.36)

        drawIcon(icon, painter, rect, state)

    def setDualText(self, large_text: str, small_text: str):
        self._large_text = large_text
        self._small_text = small_text
        self.update()

    def setFontSizes(self, large_size: int, small_size: int):
        self._large_size = large_size
        self._small_size = small_size
        self.update()

    def setTextSpacing(self, spacing: int):
        self._spacing = spacing
        self.update()

    def hasDualText(self) -> bool:
        return bool(self._large_text and self._small_text)

    def setText(self, text: str):
        super().setText(text)
        self._large_text = text
        self._small_text = ""
        self.update()

    def sizeHint(self) -> QSize:
        hint = super().sizeHint()
        if self.hasDualText():
            large_font = QFont(cfg.FontFamily.value, self._large_size)
            small_font = QFont(cfg.FontFamily.value, self._small_size)

            fm_large = QFontMetrics(large_font)
            fm_small = QFontMetrics(small_font)

            width = fm_large.width(self._large_text) + fm_small.width(self._small_text) + self._spacing
            height = max(fm_large.height(), fm_small.height()) + 12

            if width + 24 > hint.width():
                hint.setWidth(width + 24)

            if height > hint.height():
                hint.setHeight(height)
        return hint

    def setTextColor(self, hex_color: str):
        try:
            self._custom_color = QColor(hex_color)
            if not self._custom_color.isValid():
                self._custom_color = None
            self.update()
        except:
            self._custom_color = None

    def paintEvent(self, event):
        if not self.hasDualText():
            return super().paintEvent(event)

        opt = QStyleOptionButton()
        self.initStyleOption(opt)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self.style().drawControl(QStyle.CE_PushButton, opt, painter, self)

        if not self.icon().isNull():
            icon_rect = self.style().subElementRect(QStyle.SE_PushButtonContents, opt, self)
            icon_rect.setWidth(min(icon_rect.width(), 32))
            self._drawIcon(self.icon(), painter, icon_rect, opt.state & QStyle.State_On)

        content_rect = self.style().subElementRect(QStyle.SE_PushButtonContents, opt, self)

        large_font = QFont(cfg.FontFamily.value, self._large_size)
        small_font = QFont(cfg.FontFamily.value, self._small_size)

        fm_large = QFontMetrics(large_font)
        fm_small = QFontMetrics(small_font)

        large_width = fm_large.width(self._large_text)
        small_width = fm_small.width(self._small_text)
        total_width = large_width + small_width + self._spacing

        start_x = content_rect.x() + (content_rect.width() - total_width) / 2
        if not self.icon().isNull():
            start_x += content_rect.width() * 0.1

        base_y = content_rect.y() + (content_rect.height() + fm_large.ascent()) / 2 - fm_large.descent()

        color = self._custom_color
        if self._custom_color is not None:
            color = self._custom_color
        elif not self.isEnabled():
            color = QColor(0, 0, 0, 109)
        elif self.styleSheet():
            style = self.styleSheet()
            color_match = re.search(r'color:\s*(rgba?\([^)]+\)|#[0-9a-fA-F]{6,8})', style)
            if color_match:
                color_str = color_match.group(1)
                if color_str.startswith('rgb'):
                    values = re.findall(r'\d+', color_str)
                    if len(values) >= 3:
                        r, g, b = map(int, values[:3])
                        a = int(values[3]) if len(values) > 3 else 255
                        color = QColor(r, g, b, a)
                else:
                    color = QColor(color_str)
            else:
                color = QColor(0, 159, 170)
        else:
            color = QColor(0, 159, 170)

        painter.setPen(color)

        painter.setFont(large_font)
        painter.drawText(int(start_x), int(base_y), self._large_text)

        painter.setFont(small_font)
        painter.drawText(int(start_x + large_width + self._spacing), int(base_y), self._small_text)

        painter.end()

    def text(self) -> str:
        return self._large_text if self.hasDualText() else super().text()

    url = pyqtProperty(QUrl, getUrl, setUrl)


class CardWidget(BackgroundAnimationWidget, QFrame):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._isClickEnabled = False
        self._borderRadius = 5
        self._gradientStartColor = QColor()
        self._gradientEndColor = QColor()
        self.topHeight = 50

        self._styleIndex = 0
        """
        _styleIndex
        
        0 -> Normal Style
        1 -> Weather Style
        2 -> Motto Style; Curriculum Style
        3 -> Countdown Style
        """

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.clicked.emit()

    def setClickEnabled(self, isEnabled: bool):
        self._isClickEnabled = isEnabled
        self.update()

    def isClickEnabled(self):
        return self._isClickEnabled

    def _normalBackgroundColor(self):
        return QColor(255, 255, 255, 13 if isDarkTheme() else 170)

    def _hoverBackgroundColor(self):
        return QColor(255, 255, 255, 21 if isDarkTheme() else 64)

    def _pressedBackgroundColor(self):
        return QColor(255, 255, 255, 8 if isDarkTheme() else 64)

    def getBorderRadius(self):
        return self._borderRadius

    def setBorderRadius(self, radius: int):
        self._borderRadius = radius
        self.update()

    def setNormalStyle(self):
        self._styleIndex = 0
        self.update()

    def setWeatherStyle(self, startColorHex: str, endColorHex: str):
        self._styleIndex = 1
        self._gradientStartColor = QColor(f"#{startColorHex}")
        self._gradientEndColor = QColor(f"#{endColorHex}")
        self.update()

    def setMottoStyle(self):
        self._styleIndex = 2
        self.update()

    def setCountdownStyle(self):
        self._styleIndex = 3
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        r = self.borderRadius
        d = 2 * r

        isDark = isDarkTheme()

        path = QPainterPath()
        path.arcMoveTo(1, h - d - 1, d, d, 240)
        path.arcTo(1, h - d - 1, d, d, 225, -60)
        path.lineTo(1, r)
        path.arcTo(1, 1, d, d, -180, -90)
        path.lineTo(w - r, 1)
        path.arcTo(w - d - 1, 1, d, d, 90, -90)
        path.lineTo(w - 1, h - r)
        path.arcTo(w - d - 1, h - d - 1, d, d, 0, -60)

        topBorderColor = QColor(0, 0, 0, 20)
        if isDark:
            if self.isPressed:
                topBorderColor = QColor(255, 255, 255, 18)
            elif self.isHover:
                topBorderColor = QColor(255, 255, 255, 13)
        else:
            topBorderColor = QColor(0, 0, 0, 15)

        painter.strokePath(path, topBorderColor)

        path = QPainterPath()
        path.arcMoveTo(1, h - d - 1, d, d, 240)
        path.arcTo(1, h - d - 1, d, d, 240, 30)
        path.lineTo(w - r - 1, h - 1)
        path.arcTo(w - d - 1, h - d - 1, d, d, 270, 30)

        bottomBorderColor = topBorderColor
        if not isDark and self.isHover and not self.isPressed:
            bottomBorderColor = QColor(0, 0, 0, 27)

        painter.strokePath(path, bottomBorderColor)

        painter.setPen(Qt.NoPen)
        rect = self.rect().adjusted(1, 1, -1, -1)

        if self._styleIndex == 1:
            gradient = QLinearGradient(0, 0, w, h)
            gradient.setColorAt(0, self._gradientStartColor)
            gradient.setColorAt(1, self._gradientEndColor)
            painter.setBrush(gradient)

        elif self._styleIndex == 2:
            roundedPath = QPainterPath()
            roundedPath.addRoundedRect(QRectF(rect), r, r)
            painter.setClipPath(roundedPath)
            if isDark:
                acrylicColor = QColor(39, 39, 39, 180)
            else:
                acrylicColor = QColor(249, 249, 249, 180)
            painter.fillRect(rect, acrylicColor)
            highlightColor = QColor(255, 255, 255, 80 if isDark else 50)
            gradient = QLinearGradient(0, 0, 0, h)
            gradient.setColorAt(0, highlightColor)
            gradient.setColorAt(0.5, QColor(0, 0, 0, 0))
            painter.fillRect(rect, gradient)
            painter.setClipping(False)

        elif self._styleIndex == 3:
            roundedPath = QPainterPath()
            roundedPath.addRoundedRect(QRectF(rect), r, r)
            painter.setClipPath(roundedPath)
            upperRect = QRect(rect.left(), rect.top(), rect.width(), self.topHeight)
            painter.fillRect(upperRect, QColor("#990000"))
            lowerRect = QRect(rect.left(), rect.top() + self.topHeight, rect.width(), rect.height() - self.topHeight)
            painter.fillRect(lowerRect, QColor(255, 255, 255, 170 if not isDark else 13))
            painter.setClipping(False)

        else:
            painter.setBrush(self.backgroundColor)

        painter.drawRoundedRect(rect, r, r)

    borderRadius = pyqtProperty(int, getBorderRadius, setBorderRadius)


class WeatherThread(QThread):
    weather_updated = pyqtSignal()
    weather_error = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.isThreadRunning = True
        self.data = {}

    def run(self):
        while self.isThreadRunning:
            try:
                self.data = requests.get("http://10.181.201.165:1908/api/weather", timeout=5).json()
                self.weather_updated.emit()
            except:
                self.weather_error.emit()
            time.sleep(5 * 60 * 1000)


class WeatherInterface(QWidget):
    styleChanged = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.gridLayout = QGridLayout(self)
        self.gridLayout.setContentsMargins(10, 10, 10, 10)
        self.gridLayout.setVerticalSpacing(8)
        self.gridLayout.setHorizontalSpacing(16)

        self.skycon = ""
        self.iconLabel = ImageLabel(self)
        self.iconLabel.setBorderRadius(0, 0, 0, 0)
        self.titleLabel = WeatherTitleLabel(self)
        self.titleLabel.setTextColor(QColor("white"))
        self.contentLabel = WeatherContentLabel(self)
        self.contentLabel.setWordWrap(True)
        self.contentLabel.setTextColor(QColor("white"))

        self.iconLabel.setImage(":/LOADING.svg")
        self.iconLabel.setFixedSize(48, 48)
        self.titleLabel.setText("--°")
        self.contentLabel.setText("暂无数据")

        self.gridLayout.addWidget(self.iconLabel, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.titleLabel, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.contentLabel, 1, 0, 1, 2)

    def updateWeather(self):
        if self.contentLabel.text() == "暂无数据":
            self.styleChanged.emit("2f2cbc", "4bb4f0")
        elif "DAY" in self.skycon:
            self.styleChanged.emit("2f2cbc", "4bb4f0")
        elif "NIGHT" in self.skycon:
            self.styleChanged.emit("06050e", "233075")
        elif "RAIN" in self.skycon or "HAZE" in self.skycon:
            self.styleChanged.emit("172830", "57758d")
        elif "SNOW" in self.skycon:
            self.styleChanged.emit("b1ccea", "afcee2")
        elif self.skycon == "CLOUDY" or self.skycon == "FOG" or self.skycon == "WIND":
            self.styleChanged.emit("9bc0da", "cee4f1")
        elif self.skycon == "DUST" or self.skycon == "SAND":
            self.styleChanged.emit("d5b603", "ddab5f")
        else:
            self.styleChanged.emit("2f2cbc", "4bb4f0")


class MottoThread(QThread):
    motto_updated = pyqtSignal()
    motto_error = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.isThreadRunning = True
        self.data = {}

    def run(self):
        while self.isThreadRunning:
            try:
                self.data = requests.get("http://10.181.201.165:1908/api/pdb/sentence/today", timeout=5).json()
                self.motto_updated.emit()
            except:
                self.motto_error.emit()
            time.sleep(5 * 60 * 1000)


class MottoInterface(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(10, 10, 10, 10)

        self.chineseLabel = MottoLabel(self)
        self.englishLabel = MottoLabel(self)
        self.chineseLabel.setWordWrap(True)
        self.englishLabel.setWordWrap(True)
        self.chineseLabel.setTextColor(QColor("black"))
        self.englishLabel.setTextColor(QColor("grey"))

        self.vBoxLayout.addWidget(self.chineseLabel)
        self.vBoxLayout.addWidget(self.englishLabel)

        self.chineseLabel.setText("")
        self.englishLabel.setText("暂无数据")
        self.chineseLabel.setHidden(True)
        self.englishLabel.setAlignment(Qt.AlignCenter)


class CountdownInterface(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.redBlock = QWidget(self)
        self.redBlock.setFixedHeight(32)
        self.redLayout = QVBoxLayout(self.redBlock)
        self.redLayout.setContentsMargins(0, 0, 0, 0)
        self.eventLabel = CountdownEventLabel(self)
        self.eventLabel.setTextColor(QColor("white"))
        self.eventLabel.setAlignment(Qt.AlignCenter)
        self.redLayout.addWidget(self.eventLabel, alignment=Qt.AlignCenter)

        self.whiteBlock = QWidget(self)
        self.whiteLayout = QVBoxLayout(self.whiteBlock)
        self.whiteLayout.setContentsMargins(0, 0, 0, 0)
        self.displayLabel = CountdownDisplayLabel(self)
        self.displayLabel.setAlignment(Qt.AlignCenter)
        self.whiteLayout.addWidget(self.displayLabel, alignment=Qt.AlignCenter)
        self.updateCountdown()

        self.mainLayout.addWidget(self.redBlock)
        self.mainLayout.addWidget(self.whiteBlock)
        self.setLayout(self.mainLayout)

    def updateCountdown(self):
        if cfg.Event.value and cfg.Date.value:
            self.eventLabel.setText(cfg.Event.value)
            days_diff = QDate.currentDate().daysTo(QDate.fromString(cfg.Date.value, "yyyyMMdd"))
            self.displayLabel.setText(str(days_diff))
        else:
            self.eventLabel.setText("无事件")
            self.displayLabel.setText("--")


class IntegratedCard(CardWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.skyconMap = {
            "CLEAR_DAY": "CLEAR_DAY",
            "CLEAR_NIGHT": "CLEAR_NIGHT",
            "PARTLY_CLOUDY_DAY": "PARTLY_CLOUDY_DAY",
            "PARTLY_CLOUDY_NIGHT": "PARTLY_CLOUDY_NIGHT",
            "CLOUDY": "CLOUDY",
            "LIGHT_HAZE": "HAZE",
            "MODERATE_HAZE": "HAZE",
            "HEAVY_HAZE": "HAZE",
            "LIGHT_RAIN": "LIGHT_RAIN",
            "MODERATE_RAIN": "MODERATE_RAIN",
            "HEAVY_RAIN": "HEAVY_RAIN",
            "STORM_RAIN": "HEAVY_RAIN",
            "FOG": "FOG",
            "LIGHT_SNOW": "LIGHT_SNOW",
            "MODERATE_SNOW": "MODERATE_SNOW",
            "HEAVY_SNOW": "HEAVY_SNOW",
            "STORM_SNOW": "HEAVY_SNOW",
            "DUST": "DUST",
            "SAND": "DUST",
            "WIND": "WIND"
        }

        self.setFixedSize(200, 200)
        self.setBorderRadius(18)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(11, 11, 11, 11)
        self.vBoxLayout.setSpacing(15)

        self.hPager = HorizontalPipsPager(self)
        self.hPager.setPageNumber(3)
        self.hPager.setVisibleNumber(3)
        self.hPager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ON_HOVER)
        self.hPager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ON_HOVER)
        self.pagerLayout = QHBoxLayout(self)
        self.pagerLayout.setContentsMargins(0, 0, 0, 0)
        self.pagerLayout.addWidget(self.hPager)

        self.stackedWidget = QStackedWidget(self)
        self.weatherInterface = WeatherInterface(self)
        self.mottoInterface = MottoInterface(self)
        self.countdownInterface = CountdownInterface(self)
        self.weatherInterface.styleChanged.connect(self.setWeatherStyle)

        self.stackedWidget.addWidget(self.weatherInterface)
        self.stackedWidget.addWidget(self.mottoInterface)
        self.stackedWidget.addWidget(self.countdownInterface)

        self.hPager.currentIndexChanged.connect(self.stackedWidget.setCurrentIndex)
        self.stackedWidget.currentChanged.connect(self.hPager.setCurrentIndex)
        self.hPager.currentIndexChanged.connect(self.updateStyle)

        self.grabGesture(Qt.PanGesture)
        self.grabGesture(Qt.SwipeGesture)
        self.startPos = QPoint()

        self.vBoxLayout.addWidget(self.stackedWidget, Qt.AlignHCenter)
        self.vBoxLayout.addLayout(self.pagerLayout)
        self.updateStyle()

        self.timer = QTimer()
        self.timer.timeout.connect(self.onTimeOut)
        self.timer.start(10000)

        self.weatherThread = WeatherThread()
        self.weatherThread.weather_updated.connect(self.onWeatherUpdated)
        self.weatherThread.weather_error.connect(self.onWeatherError)
        self.weatherThread.start()
        self.mottoThread = MottoThread()
        self.mottoThread.motto_updated.connect(self.onMottoUpdated)
        self.mottoThread.motto_error.connect(self.onMottoError)
        self.mottoThread.start()

    def event(self, event):
        if event.type() == QEvent.Gesture:
            return self.gestureEvent(event)

        elif event.type() == QEvent.TouchBegin:
            self.startPos = event.touchPoints()[0].pos()
            return True
        elif event.type() == QEvent.TouchEnd:
            endPos = event.touchPoints()[0].pos()
            diffX = endPos.x() - self.startPos.x()
            if abs(diffX) > 30:
                currentIndex = self.stackedWidget.currentIndex()
                totalPages = self.stackedWidget.count()
                if diffX < 0 and currentIndex < totalPages - 1:
                    self.stackedWidget.setCurrentIndex(currentIndex + 1)
                    self.updateStyle()
                elif diffX > 0 and currentIndex > 0:
                    self.stackedWidget.setCurrentIndex(currentIndex - 1)
                    self.updateStyle()
            return True
        return super().event(event)

    def gestureEvent(self, event):
        swipe = event.gesture(Qt.SwipeGesture)
        if swipe:
            if swipe.state() == Qt.GestureFinished:
                if swipe.horizontalDirection() == QSwipeGesture.Left:
                    currentIndex = self.stackedWidget.currentIndex()
                    if currentIndex < self.stackedWidget.count() - 1:
                        self.stackedWidget.setCurrentIndex(currentIndex + 1)
                        self.updateStyle()
                elif swipe.horizontalDirection() == QSwipeGesture.Right:
                    currentIndex = self.stackedWidget.currentIndex()
                    if currentIndex > 0:
                        self.stackedWidget.setCurrentIndex(currentIndex - 1)
                        self.updateStyle()
                return True

        pan = event.gesture(Qt.PanGesture)
        if pan:
            return True

        return False

    def onTimeOut(self):
        currentIndex = self.stackedWidget.currentIndex()
        if currentIndex == 0:
            self.stackedWidget.setCurrentIndex(1)
            self.setMottoStyle()
        elif currentIndex == 1:
            self.stackedWidget.setCurrentIndex(2)
            self.setCountdownStyle()
        elif currentIndex == 2:
            self.stackedWidget.setCurrentIndex(0)
            self.weatherInterface.updateWeather()

    def onWeatherUpdated(self):
        self.weatherInterface.titleLabel.setText(f"{round(self.weatherThread.data['result']['realtime']['temperature'])}°")
        self.weatherInterface.contentLabel.setText(f"{self.weatherThread.data['result']['forecast_keypoint']}")
        icon = self.skyconMap.get(self.weatherThread.data['result']['realtime']['skycon'], "LOADING")
        self.weatherInterface.iconLabel.setImage(f":/{icon}.svg")
        self.weatherInterface.iconLabel.setFixedSize(48, 48)
        self.weatherInterface.skycon = self.weatherThread.data['result']['realtime']['skycon']

    def onWeatherError(self):
        self.weatherInterface.iconLabel.setImage(":/LOADING.svg")
        self.weatherInterface.iconLabel.setFixedSize(48, 48)
        self.weatherInterface.titleLabel.setText("--°")
        self.weatherInterface.contentLabel.setText("暂无数据")
        self.weatherInterface.skycon = ""

    def onMottoUpdated(self):
        self.mottoInterface.chineseLabel.setText(self.mottoThread.data['chs'])
        self.mottoInterface.englishLabel.setText(self.mottoThread.data['eng'])
        self.mottoInterface.chineseLabel.setHidden(False)
        self.mottoInterface.englishLabel.setAlignment(Qt.AlignLeft)

    def onMottoError(self):
        self.mottoInterface.chineseLabel.setText("")
        self.mottoInterface.englishLabel.setText("暂无数据")
        self.mottoInterface.chineseLabel.setHidden(True)
        self.mottoInterface.englishLabel.setAlignment(Qt.AlignCenter)

    def updateStyle(self):
        if self.hPager.currentIndex() == 0:
            self.weatherInterface.updateWeather()
        elif self.hPager.currentIndex() == 1:
            self.setMottoStyle()
        elif self.hPager.currentIndex() == 2:
            self.setCountdownStyle()


class CurriculumCard(CardWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setBorderRadius(18)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.setMottoStyle()

        self.nullLabel = MottoLabel(self)
        self.nullLabel.setTextColor(QColor('grey'))
        self.nullLabel.setText("无课程")
        self.nullLabel.setHidden(True)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.scrollArea = SmoothScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.enableTransparentBackground()

        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.contentWidget = QWidget()
        self.contentWidget.setStyleSheet("background: transparent;")
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(25, 10, 10, 10)
        self.contentLayout.setSpacing(0)
        self.contentLayout.addWidget(self.nullLabel, Qt.AlignCenter)

        self.scrollArea.setWidget(self.contentWidget)
        self.mainLayout.addWidget(self.scrollArea)

        dayOfWeek = QDate.currentDate().dayOfWeek()
        if dayOfWeek == 1:
            lst = cfg.Mon.value
        elif dayOfWeek == 2:
            lst = cfg.Tue.value
        elif dayOfWeek == 3:
            lst = cfg.Wed.value
        elif dayOfWeek == 4:
            lst = cfg.Thu.value
        elif dayOfWeek == 5:
            lst = cfg.Fri.value
        elif dayOfWeek == 6:
            lst = cfg.Sat.value
        else:
            lst = cfg.Sun.value

        if lst:
            for item in lst:
                btn = CurriculumButton(self.contentWidget)
                if str(item[1]):
                    btn.setDualText(str(item[0]), str(item[1]))
                else:
                    btn.setDualText(str(item[0]), ' ')
                btn.setFixedWidth(150)
                btn.setTextColor(cfg.FontColor.value)

                if item[2]:
                    btn.setUrl(QUrl.fromLocalFile(str(item[2])))
                    btn.setToolTip(str(item[2]))
                    btn.installEventFilter(ToolTipFilter(btn, 0, ToolTipPosition.BOTTOM))

                self.contentLayout.addWidget(btn, Qt.AlignCenter)
        else:
            self.nullLabel.setHidden(False)

        self.contentLayout.addStretch()

        if self.scrollArea and self.contentWidget:
            contentHeight = self.contentWidget.sizeHint().height()
            maxHeight = QApplication.desktop().availableGeometry().height() - 260
            if contentHeight > maxHeight:
                self.setFixedHeight(maxHeight)
                self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            elif contentHeight <= 400:
                self.setFixedHeight(400)
                self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            else:
                self.setFixedHeight(contentHeight)
                self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


class Main(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neon")
        self.setWindowIcon(QIcon(':/icon.png'))
        self.resize(250, QApplication.desktop().availableGeometry().height())
        self.move(QApplication.desktop().availableGeometry().width() - 250, 0)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(6)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)

        self.integratedCard = IntegratedCard(self)
        self.curriculumCard = CurriculumCard(self)
        self.vBoxLayout.addStretch()
        self.vBoxLayout.addWidget(self.integratedCard)
        self.vBoxLayout.addWidget(self.curriculumCard)
        self.vBoxLayout.addStretch()

        self._tray_icon_menu = RoundMenu()
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(":/icon.png"))
        self.tray_icon.setToolTip("Neon")
        self.createActions()
        self.createTrayIcon()
        self.tray_icon.activated.connect(self.trayIconActivated)

    def trayIconActivated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger or reason == QSystemTrayIcon.ActivationReason.Context:
            self._tray_icon_menu.exec(self.tray_icon.geometry().center())

    def createActions(self):
        self._refresh_action = QAction(FluentFontIcon("\ue72c").icon(), "刷新", parent=self)
        self._refresh_action.triggered.connect(self.refresh)

        self._setting_action = QAction(FluentFontIcon("\ue713").icon(), "设置", self)
        self._help_action = QAction(FluentFontIcon("\uea6b").icon(), "帮助", self)
        self._setting_action.triggered.connect(self.openSetting)
        # self._help_action.triggered.connect()

        self._hide_action = QAction(FluentFontIcon("\uecc9").icon(), "隐藏", parent=self)
        self._restore_action = QAction(FluentFontIcon("\uecc8").icon(), "显示", parent=self)
        self._hide_action.triggered.connect(self.hide)
        self._restore_action.triggered.connect(self.show)

        self._quit_action = QAction(FluentFontIcon("\ue7e8").icon(), "退出", self)
        self._quit_action.triggered.connect(self.quitApp)

    def createTrayIcon(self):
        self._tray_icon_menu.addAction(self._refresh_action)
        self._tray_icon_menu.addSeparator()
        self._tray_icon_menu.addAction(self._setting_action)
        self._tray_icon_menu.addAction(self._help_action)
        self._tray_icon_menu.addSeparator()
        self._tray_icon_menu.addAction(self._restore_action)
        self._tray_icon_menu.addAction(self._hide_action)
        self._tray_icon_menu.addSeparator()
        self._tray_icon_menu.addAction(self._quit_action)
        self.tray_icon.setContextMenu(self._tray_icon_menu)
        self.tray_icon.show()

    def refresh(self):
        self.integratedCard.weatherThread.isThreadRunning = False
        self.integratedCard.mottoThread.isThreadRunning = False
        self.integratedCard.weatherThread.terminate()
        self.integratedCard.mottoThread.terminate()

        self.integratedCard.weatherThread = WeatherThread()
        self.integratedCard.mottoThread = MottoThread()

        self.integratedCard.weatherThread.weather_updated.connect(self.integratedCard.onWeatherUpdated)
        self.integratedCard.weatherThread.weather_error.connect(self.integratedCard.onWeatherError)
        self.integratedCard.mottoThread.motto_updated.connect(self.integratedCard.onMottoUpdated)
        self.integratedCard.mottoThread.motto_error.connect(self.integratedCard.onMottoError)

        self.integratedCard.weatherThread.start()
        self.integratedCard.mottoThread.start()

        self.integratedCard.countdownInterface.updateCountdown()

    def openSetting(self):
        os.startfile(os.path.abspath("./config/config.json"))

    def quitApp(self):
        self.hide()

        self.integratedCard.weatherThread.isThreadRunning = False
        self.integratedCard.mottoThread.isThreadRunning = False
        self.integratedCard.weatherThread.terminate()
        self.integratedCard.mottoThread.terminate()

        QApplication.quit()


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = Main()
    w.show()
    app.exec()
