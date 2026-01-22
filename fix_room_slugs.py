#!/usr/bin/env python
"""
修复ForumRoom表中空slug的脚本
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WhynotEnglish.settings')
django.setup()

from social.models import ForumRoom
from django.utils.text import slugify

def fix_room_slugs():
    """为没有slug的房间生成slug"""
    rooms_without_slug = ForumRoom.objects.filter(slug='')
    
    print(f"找到 {rooms_without_slug.count()} 个没有slug的房间")
    
    for room in rooms_without_slug:
        # 生成slug
        new_slug = slugify(room.name)
        print(f"房间: {room.name} -> slug: {new_slug}")
        
        # 如果slugify返回空字符串（如纯中文），使用UUID
        if not new_slug:
            import uuid
            new_slug = f"room-{uuid.uuid4().hex[:8]}"
        
        # 检查slug是否已存在
        if ForumRoom.objects.filter(slug=new_slug).exclude(id=room.id).exists():
            # 如果存在，添加数字后缀
            counter = 1
            original_slug = new_slug
            while ForumRoom.objects.filter(slug=new_slug).exclude(id=room.id).exists():
                new_slug = f"{original_slug}-{counter}"
                counter += 1
        
        # 保存slug
        room.slug = new_slug
        room.save()
        print(f"[OK] 已更新: {room.name} -> {room.slug}")
    
    print("[SUCCESS] 所有房间slug修复完成!")

if __name__ == "__main__":
    fix_room_slugs()