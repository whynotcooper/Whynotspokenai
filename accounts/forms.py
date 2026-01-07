# accounts/forms.py
from django import forms
from django.core.validators import RegexValidator, MinLengthValidator
from spoken_ai.models import UserInfoModel


class LoginForm(forms.Form):
    username = forms.CharField(label="用户名/手机号", max_length=100)
    password = forms.CharField(label="密码", widget=forms.PasswordInput)


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput,
        validators=[MinLengthValidator(10, message="密码必须至少10位")]
    )
    password2 = forms.CharField(label="确认密码", widget=forms.PasswordInput)

    class Meta:
        model = UserInfoModel
        fields = ["username", "phone", "avatar", "english_level"]

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if not username:
            raise forms.ValidationError("用户名不能为空")
        # 复用你模型里的规则
        RegexValidator(
            regex='^[a-zA-Z0-9_]+$',
            message='用户名只能包含字母、数字和下划线',
            code='invalid_username'
        )(username)
        if UserInfoModel.objects.filter(username=username).exists():
            raise forms.ValidationError("用户名已存在")
        return username

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        RegexValidator(
            regex='^1[3-9]\\d{9}$',
            message='请输入有效的手机号',
            code='invalid_phone'
        )(phone)
        if UserInfoModel.objects.filter(phone=phone).exists():
            raise forms.ValidationError("手机号已存在")
        return phone

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password2"):
            self.add_error("password2", "两次密码不一致")
        return cleaned
# accounts/forms.py
from django import forms
from spoken_ai.models import UserInfoModel

class RegisterForm(forms.ModelForm):
    password = forms.CharField(min_length=10, widget=forms.PasswordInput)
    password2 = forms.CharField(min_length=10, widget=forms.PasswordInput)

    class Meta:
        model = UserInfoModel
        fields = ["username", "phone", "english_level"]  # avatar 你若不在注册传，就别放
        # 如果你注册也要传头像：把 avatar 加进 fields

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password2"):
            self.add_error("password2", "两次密码不一致")
        return cleaned
