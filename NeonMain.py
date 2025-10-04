# -*- coding: utf-8 -*-

import sys
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize, pyqtProperty, QRect, QRectF, QEvent
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QLinearGradient
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QStackedWidget, QWidget, \
    QGridLayout, QListWidget, QListWidgetItem, QFrame, QSwipeGesture
from qfluentwidgets import BodyLabel, FluentIcon, isDarkTheme, MSFluentTitleBar, HorizontalPipsPager, \
    PipsScrollButtonDisplayMode, ImageLabel, TitleLabel, SmoothScrollBar, FluentStyleSheet, ToolTipFilter, \
    ToolTipPosition, StrongBodyLabel, DisplayLabel, SubtitleLabel
from qfluentwidgets.common.animation import BackgroundAnimationWidget
from qfluentwidgets.components.widgets.pips_pager import PipsDelegate, ScrollButton
from qfluentwidgets.common.overload import singledispatchmethod


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


if isWin11():
    from qframelesswindow import AcrylicWindow as Window
else:
    from qframelesswindow import FramelessWindow as Window


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
            self.preButton.move(0, int(h/2 - bh/2))
            self.nextButton.move(w - bw, int(h/2 - bh/2))
        else:
            self.preButton.move(int(w/2-bw/2), 0)
            self.nextButton.move(int(w/2-bw/2), h-bh)

    visibleNumber = pyqtProperty(int, getVisibleNumber, setVisibleNumber)
    pageNumber = pyqtProperty(int, getPageNumber, setPageNumber)


class HorizontalPipsPager(PipsPager):
    """ Horizontal pips pager """

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)


class CardWidget(BackgroundAnimationWidget, QFrame):
    """ Card widget """

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
        2 -> Motto Style
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

            upperRect = QRect(rect.left(), rect.top(), rect.width(), rect.height() // 2)
            painter.fillRect(upperRect, QColor("#e9aa0c"))
            lowerRect = QRect(rect.left(), rect.top() + rect.height() // 2, rect.width(), rect.height() // 2)
            painter.fillRect(lowerRect, QColor("#f0d35d"))

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


class WeatherInterface(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.gridLayout = QGridLayout(self)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)

        self.iconLabel = ImageLabel("WeatherIcon/CLEAR_DAY.svg")
        self.iconLabel.setFixedSize(48, 48)
        self.iconLabel.setBorderRadius(0, 0, 0, 0)
        self.titleLabel = TitleLabel(self)
        self.titleLabel.setTextColor(QColor("white"))
        self.contentLabel = BodyLabel(self)
        self.contentLabel.setWordWrap(True)
        self.contentLabel.setTextColor(QColor("white"))


        self.titleLabel.setText("28-32°")
        self.contentLabel.setText("未来2小时内无雨，放心出门吧。")

        self.gridLayout.addWidget(self.iconLabel, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.titleLabel, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.contentLabel, 1, 0, 1, 2)


class MottoInterface(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.chineseLabel = StrongBodyLabel(self)
        self.englishLabel = BodyLabel(self)
        self.chineseLabel.setWordWrap(True)
        self.englishLabel.setWordWrap(True)
        self.englishLabel.setTextColor(QColor("grey"))

        self.chineseLabel.setText("你若盛开，清风自来。")
        self.englishLabel.setText("If you look at what you have in life, you'll always have more.")

        self.vBoxLayout.addWidget(self.chineseLabel)
        self.vBoxLayout.addWidget(self.englishLabel)


class CountdownInterface(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.eventLabel = SubtitleLabel(self)
        self.displayLabel = DisplayLabel(self)
        self.eventLabel.setTextColor(QColor("white"))
        self.eventLabel.setAlignment(Qt.AlignCenter)
        self.displayLabel.setAlignment(Qt.AlignCenter)

        self.eventLabel.setText("首考")
        self.displayLabel.setText("99")

        self.vBoxLayout.addWidget(self.eventLabel)
        self.vBoxLayout.addWidget(self.displayLabel)


class IntegratedCardWidget(CardWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
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

    def updateStyle(self):
        if self.hPager.currentIndex() == 0:
            self.setWeatherStyle("2f2cbc", "4bb4f0")
        elif self.hPager.currentIndex() == 1:
            self.setMottoStyle()
        elif self.hPager.currentIndex() == 2:
            self.setCountdownStyle()


class MicaWindow(Window):

    def __init__(self):
        super().__init__()
        self.setTitleBar(MSFluentTitleBar(self))
        if isWin11():
            self.windowEffect.setMicaEffect(self.winId(), isDarkTheme())


class Main(MicaWindow):

    def __init__(self):
        super().__init__()
        self.resize(600, 600)

        self.vBoxLayout = QVBoxLayout(self)

        self.vBoxLayout.setSpacing(6)
        self.vBoxLayout.setContentsMargins(30, 60, 30, 30)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.integratedWidgetCard = IntegratedCardWidget(self)
        self.vBoxLayout.addWidget(self.integratedWidgetCard, alignment=Qt.AlignTop)


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = Main()
    w.show()
    app.exec()
