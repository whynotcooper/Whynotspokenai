# social/forms.py
from django import forms
from spoken_ai.models import UserInfoModel
from .models import UserProfile




class AvatarForm(forms.ModelForm):
    class Meta:
        model = UserInfoModel
        fields = ["avatar"]
        widgets = {
            "avatar": forms.ClearableFileInput(attrs={
                "accept": "image/*",
                "id": "avatarInput",   # 给 JS 用
            })
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["nickname", "bio"]
        widgets = {
            "nickname": forms.TextInput(attrs={"class": "input", "placeholder": "请输入昵称"}),
            "bio": forms.Textarea(attrs={"class": "input", "placeholder": "写点什么…"}),
        }
