from django import forms
from django.forms import Textarea

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", "image")
        labels = {
            "group": ("Группа"),
            "text": ("Текст"),
            "image": ("Картинка"),
        }

        help_texts = {
            "group": ("Выберите группу для новой записи"),
            "text": ("Добавьте текст для новой записи")
        }

    def clean_text(self):
        data = self.cleaned_data["text"]
        if data == "":
            raise forms.ValidationError(
                "А кто поле будет заполнять, Пушкин?"
            )
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        labels = {
            "text": ("Текст"),
        }
        help_texts = {
            "text": ("Добавьте комментарий")
        }
        widgets = {
            "text": Textarea(attrs={"class": "form-control"})
        }

    def clean_text(self):
        data = self.cleaned_data["text"]
        if data == "":
            raise forms.ValidationError(
                "Заполните поле для отправки комментария"
            )
        return data
