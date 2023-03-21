# Generated by Django 2.2.19 on 2023-03-11 06:48

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0003_add_ingredients'),
    ]

    operations = [
        migrations.CreateModel(
            name='FavouriteRecipe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Избранный рецепты',
                'verbose_name_plural': 'Избранные рецепты',
            },
        ),
        migrations.AlterModelOptions(
            name='ingredientsrecipe',
            options={'verbose_name': 'Ингредиент для рецепта', 'verbose_name_plural': 'Ингредиенты для рецептов'},
        ),
        migrations.AlterModelOptions(
            name='recipes',
            options={'ordering': ('-id',), 'verbose_name': 'Рецепт', 'verbose_name_plural': 'Рецепты'},
        ),
        migrations.AlterModelOptions(
            name='shoppingcartrecipe',
            options={'verbose_name': 'Рецепт в корзине покупок', 'verbose_name_plural': 'Рецепты в корзине покупок'},
        ),
        migrations.AlterModelOptions(
            name='tags',
            options={'verbose_name': 'Тег', 'verbose_name_plural': 'Теги'},
        ),
        migrations.RemoveField(
            model_name='recipes',
            name='is_favorited',
        ),
        migrations.DeleteModel(
            name='FavoriteRecipe',
        ),
        migrations.AddField(
            model_name='favouriterecipe',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favourited_by', to='recipes.Recipes'),
        ),
        migrations.AddField(
            model_name='favouriterecipe',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favourite_recipe', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='recipes',
            name='is_favourited',
            field=models.ManyToManyField(blank=True, default=None, related_name='favourite_recipes', through='recipes.FavouriteRecipe', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='favouriterecipe',
            unique_together={('user', 'recipe')},
        ),
    ]
