from django import forms
from spoken_ai.models import UserInfoModel
from .models import UserProfile, Post, PostImage


class AvatarForm(forms.ModelForm):
    class Meta:
        model = UserInfoModel
        fields = ["avatar"]
        widgets = {
            "avatar": forms.ClearableFileInput(attrs={
                "accept": "image/*",
                "id": "avatarInput",
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


class PostForm(forms.ModelForm):
    # ✅ 在 Form 里声明 images，但不强行用 widget multiple
    images = forms.FileField(required=False)

    class Meta:
        model = Post
        fields = ["title", "content", "is_public"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input", "placeholder": "标题（可选）"}),
            "content": forms.Textarea(attrs={"class": "input", "placeholder": "写下你的学习心得…", "rows": 8}),
        }

    def clean_images(self):
        files = self.files.getlist("images")
        if len(files) > 6:
            raise forms.ValidationError("最多只能上传 6 张图片。")
        for f in files:
            if not (getattr(f, "content_type", "") or "").startswith("image/"):
                raise forms.ValidationError("只能上传图片文件。")
        return files

    def save(self, author=None, commit=True):
        post = super().save(commit=False)
        if author is not None:
            post.author = author

        if commit:
            post.save()
            files = self.files.getlist("images")
            for idx, f in enumerate(files):
                PostImage.objects.create(post=post, image=f, order=idx)

        return post
# social/forms.py
from django import forms
from .models import PostComment

class CommentForm(forms.ModelForm):
    class Meta:
        model = PostComment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={
                "class": "c-input",
                "placeholder": "写下你的评论（建议：指出亮点表达 / 可替换句式 / 发音建议）",
                "rows": 3,
            })
        }

    def clean_content(self):
        v = (self.cleaned_data.get("content") or "").strip()
        if not v:
            raise forms.ValidationError("评论不能为空")
        if len(v) > 500:
            raise forms.ValidationError("评论最多 500 字")
        return v
