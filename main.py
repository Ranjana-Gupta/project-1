from kivy.config import Config
# Force a fixed landscape resolution (for Android, set landscape in buildozer.spec)
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '480')

from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
import random

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.boxlayout import MDBoxLayout

# A widget to draw a vertical gradient background (blue to purple) for the game.
class GradientWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.texture = self.create_gradient_texture()
        self.bind(pos=self.update_rect, size=self.update_rect)
        with self.canvas:
            self.rect = Rectangle(texture=self.texture, pos=self.pos, size=self.size)

    def create_gradient_texture(self):
        gradient_height = 64
        texture = Texture.create(size=(1, gradient_height), colorfmt='rgba')
        buf = []
        for i in range(gradient_height):
            # Interpolate: top is blue, bottom is purple.
            f = i / float(gradient_height - 1)
            r = 0.5 * f
            g = 0
            b = 1 - 0.5 * f
            a = 1
            buf.extend([int(r * 255), int(g * 255), int(b * 255), int(a * 255)])
        buf = bytes(buf)
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        texture.wrap = 'repeat'
        texture.uvsize = (Window.width, -self.height if self.height else -1)
        return texture

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

# A different background for the main menu (green to blue gradient).
class MenuBackground(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.texture = self.create_menu_gradient()
        self.bind(pos=self.update_rect, size=self.update_rect)
        with self.canvas:
            self.rect = Rectangle(texture=self.texture, pos=self.pos, size=self.size)

    def create_menu_gradient(self):
        gradient_height = 64
        texture = Texture.create(size=(1, gradient_height), colorfmt='rgba')
        buf = []
        for i in range(gradient_height):
            # Interpolate: top green, bottom blue.
            f = i / float(gradient_height - 1)
            r = 0
            g = 1 - 0.5 * f  # from green to a bit darker
            b = 0.5 + 0.5 * f  # from light blue to blue
            a = 1
            buf.extend([int(r * 255), int(g * 255), int(b * 255), int(a * 255)])
        buf = bytes(buf)
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        texture.wrap = 'repeat'
        texture.uvsize = (Window.width, -self.height if self.height else -1)
        return texture

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

# Main game widget with snake logic.
class SnakeGame(Widget):
    def __init__(self, score_label, speed, game_over_callback, **kwargs):
        super().__init__(**kwargs)
        self.score_label = score_label
        self.game_over_callback = game_over_callback
        self.snake = [(100, 100), (80, 100), (60, 100)]
        self.direction = (20, 0)  # moving right
        self.food = self.new_food()
        self.score = 0
        self.speed = speed
        self.game_clock = Clock.schedule_interval(self.update, self.speed)

    def new_food(self):
        x = random.randrange(0, int(Window.width), 20)
        y = random.randrange(0, int(Window.height), 20)
        return (x, y)

    def update(self, dt):
        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
        # End game if snake goes out-of-bounds.
        if (new_head[0] < 0 or new_head[0] >= Window.width or
            new_head[1] < 0 or new_head[1] >= Window.height):
            self.end_game()
            return

        self.snake.insert(0, new_head)
        if abs(new_head[0] - self.food[0]) < 20 and abs(new_head[1] - self.food[1]) < 20:
            self.score += 1
            self.score_label.text = f"Score: {self.score}"
            self.food = self.new_food()
        else:
            self.snake.pop()

        self.draw()

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            # Draw food (red).
            Color(1, 0, 0)
            Ellipse(pos=self.food, size=(20, 20))
            # Draw snake (green segments).
            Color(0, 1, 0)
            for pos in self.snake:
                Rectangle(pos=pos, size=(20, 20))

    def on_touch_move(self, touch):
        dx, dy = touch.dx, touch.dy
        if abs(dx) > abs(dy):
            self.direction = (20, 0) if dx > 0 else (-20, 0)
        else:
            self.direction = (0, 20) if dy > 0 else (0, -20)

    def end_game(self):
        Clock.unschedule(self.game_clock)
        self.game_over_callback(self.score)

# Game screen that holds the SnakeGame.
class GameScreen(Screen):
    def __init__(self, speed, **kwargs):
        super().__init__(**kwargs)
        # Add game background.
        self.gradient = GradientWidget()
        self.add_widget(self.gradient)
        # Score label.
        self.score_label = MDLabel(
            text="Score: 0",
            halign="center",
            pos_hint={"center_x": 0.5, "top": 0.98},
            size_hint=(1, 0.1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H5"
        )
        self.add_widget(self.score_label)
        # Add the SnakeGame widget.
        self.game = SnakeGame(score_label=self.score_label, speed=speed,
                              game_over_callback=self.on_game_over)
        self.add_widget(self.game)

    def on_game_over(self, score):
        self.dialog = MDDialog(
            title="Game Over",
            text=f"Your score: {score}",
            buttons=[
                MDFlatButton(text="MENU", on_release=self.go_to_menu),
                MDRaisedButton(text="PLAY AGAIN", on_release=self.play_again)
            ]
        )
        self.dialog.open()

    def go_to_menu(self, *args):
        self.dialog.dismiss()
        app = MDApp.get_running_app()
        app.sm.current = "menu"
        app.sm.remove_widget(self)

    def play_again(self, *args):
        self.dialog.dismiss()
        app = MDApp.get_running_app()
        app.sm.remove_widget(self)
        new_game = GameScreen(name="game", speed=app.menu_screen.selected_difficulty["speed"])
        app.sm.add_widget(new_game)
        app.sm.current = "game"

# Main menu screen with title, Play, Difficulty, Info, and Quit options.
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add a custom menu background.
        self.add_widget(MenuBackground())
        layout = MDBoxLayout(orientation="vertical", spacing=20, padding=50)
        self.add_widget(layout)
        
        # Title label for the game.
        title = MDLabel(
            text="A Simple Snake Game by UFG Channel",
            halign="center",
            size_hint=(1, 0.2),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H4"
        )
        layout.add_widget(title)

        self.play_button = MDRaisedButton(
            text="Play",
            pos_hint={"center_x": 0.5},
            on_release=self.start_game
        )
        layout.add_widget(self.play_button)

        self.difficulty_options = [
            {"text": "Easy", "speed": 0.3},
            {"text": "Medium", "speed": 0.2},
            {"text": "Hard", "speed": 0.1}
        ]
        self.selected_difficulty = self.difficulty_options[1]  # default: Medium

        self.diff_button = MDRaisedButton(
            text=f"Difficulty: {self.selected_difficulty['text']}",
            pos_hint={"center_x": 0.5}
        )
        layout.add_widget(self.diff_button)

        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": opt["text"],
                "on_release": lambda opt=opt: self.set_difficulty(opt)
            } for opt in self.difficulty_options
        ]
        self.menu = MDDropdownMenu(
            caller=self.diff_button,
            items=menu_items,
            width_mult=4,
        )
        self.diff_button.bind(on_release=lambda instance: self.menu.open())

        self.info_button = MDRaisedButton(
            text="Info",
            pos_hint={"center_x": 0.5},
            on_release=self.show_info
        )
        layout.add_widget(self.info_button)

        self.quit_button = MDRaisedButton(
            text="Quit",
            pos_hint={"center_x": 0.5},
            on_release=lambda x: MDApp.get_running_app().stop()
        )
        layout.add_widget(self.quit_button)

    def set_difficulty(self, option):
        self.selected_difficulty = option
        self.diff_button.text = f"Difficulty: {option['text']}"
        self.menu.dismiss()

    def start_game(self, *args):
        app = MDApp.get_running_app()
        if "game" in app.sm.screen_names:
            app.sm.remove_widget(app.sm.get_screen("game"))
        game_screen = GameScreen(name="game", speed=self.selected_difficulty["speed"])
        app.sm.add_widget(game_screen)
        app.sm.current = "game"

    def show_info(self, *args):
        info_text = (
            "Snake Game Instructions:\n\n"
            "- Swipe to change the snake's direction.\n"
            "- Eat the red food to grow and increase your score.\n"
            "- The game ends when the snake goes out of bounds.\n"
            "- Select a difficulty to change the snake's speed.\n"
            "- Use Quit to exit the game."
        )
        dialog = MDDialog(
            title="How to Play",
            text=info_text,
            buttons=[MDFlatButton(text="Close", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()

# Main App using KivyMD's MDApp.
class SnakeApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.sm = ScreenManager()
        self.menu_screen = MenuScreen(name="menu")
        self.sm.add_widget(self.menu_screen)
        return self.sm

if __name__ == '__main__':
    SnakeApp().run()
