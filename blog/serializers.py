from rest_framework import serializers
from .models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ("title", "text", "url", "create_time")

    # 自定义模型创建方法
    def create(self, validated_data):
        return Article(**validated_data)

    # def update(self, ins, validated_data):
    #     data_mapping = {item['id']: item for item in validated_data}