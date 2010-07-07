import unittest

from django.db import models
from django.contrib.auth.models import AnonymousUser, User

from models import Favorite
from managers import FavoritesManagerMixin

class BaseFavoriteTestCase(unittest.TestCase):
    def setUp(self):
        self.users = dict([(u.username, u) for u in User.objects.all()])
        if len(self.users) != 4:
            for name in ['alice', 'bob', 'chris', 'dawn']:
                try:
                    u = User.objects.create(username=name)
                    self.users[name] = u
                except:
                    pass

class FavoriteTestCase(BaseFavoriteTestCase):
    def testAddFavorite(self):
        """ Add alice as a favorite of chris, add the favorite as a favorite 
        of alice 
        """
        chris = self.users['chris']
        alice = self.users['alice']
        favorite = Favorite.objects.create_favorite(chris, alice)

        self.assertEquals(favorite.user, chris)        
        self.assertEquals(favorite.content_object, alice)

        meta_favorite = Favorite.objects.create_favorite(alice, favorite)

        self.assertEquals(meta_favorite.user, alice)
        self.assertEquals(meta_favorite.content_object, favorite)

    def testGetFavoritesForUser(self):
        """ Get favorites for chris """
        chris = self.users['chris']
        alice = self.users['alice']

        # verify that people can get them
        favorites = Favorite.objects.favorites_for_user(chris)

        self.assertEquals(len(favorites), 1)
        self.assertEquals(favorites[0].content_object, self.users['alice'])
        
    def testGetFavoritesForModel(self):
        alice = self.users['alice']

        # the meta favorite
        meta_favorite = Favorite.objects.get(pk=2)

        favorites = Favorite.objects.favorites_for_model(Favorite)

        self.assertEquals(len(favorites), 1)
        self.assertEquals(favorites[0], meta_favorite)
        self.assertEquals(favorites[0].user, alice)

    def testGetFavoritesForObject(self):
        alice = self.users['alice']

        favorite = Favorite.objects.get(pk=1)

        favorites = Favorite.objects.favorites_for_object(favorite)
        self.assertEquals(len(favorites), 1)
        self.assertEquals(favorites[0].user, alice)

class AnimalManager(models.Manager, FavoritesManagerMixin):
    pass

class Animal(models.Model):
    name = models.CharField(max_length=20)

    objects = AnimalManager()

    def __unicode__(self):
        return self.name

class FavoritesMixinTestCase(BaseFavoriteTestCase):

    def setUp(self):
        super(FavoritesMixinTestCase, self).setUp()
        self.animals = {}
        for a in ['zebra', 'donkey', 'horse']:
            ani = Animal(name=a)
            ani.save()
            self.animals[a] = ani
            
    
    def testWithFavorites(self):
        """ Tests whether or not `with_favorite_for` works
        """
        alice = self.users['alice']
        chris = self.users['chris']

        Favorite.objects.create_favorite(self.animals['zebra'], alice)
        Favorite.objects.create_favorite(self.animals['donkey'], chris)

        zebra = Animal.objects.with_favorite_for(alice).get(name='zebra')
        self.assertEquals(zebra.favorite__favorite, 1)

        all_animals = Animal.objects.with_favorite_for(alice).all()
        self.assertEquals(len(all_animals), 3)

        favorite_animals = Animal.objects.with_favorite_for(alice, all=False).all()
        self.assertEquals(len(favorite_animals), 1)
        
    def testWithFavoritesAnon(self):
        """ Passing an anonymous user should still work, but anon users
        don't have favorites
        """
        anon = AnonymousUser()
        animals = Animal.objects.with_favorite_for(anon)
        self.assertEqual(3, len(animals))

        for animal in animals:
            self.assertEqual(0, animal.favorite__favorite)
        
        favorite_animals = Animal.objects.with_favorite_for(anon, all=False).all()
        self.assertEquals(len(favorite_animals), 0)


