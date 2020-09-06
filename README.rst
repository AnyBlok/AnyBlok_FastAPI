===============
AnyBlok FastAPI
===============

Use AnyBlok with FastAPI


* Free software: Mozilla Public License Version 2.0
* Documentation: https://anyblok-fastapi.readthedocs.io.

TODO
----

- [x] Valider le fonctionnement tel quel avec sqla et des class "schéma" / create / get
- [x] Tester une déclaration des routes dans le load du blok avec un middlware
      qui ferait un set de app.router.routes à la vollé en fonction de l'info
      stocké sur le registre
      https://fastapi.tiangolo.com/advanced/custom-request-and-route/
- [ ] Tester l'intégration gunicorn
- [ ] Gestion des exceptions (https://fastapi.tiangolo.com/tutorial/handling-errors/):
    - [ ] erreur de validation
    - [ ] erreur SQLA genre un enregistrement non trouvé avec un one
    - [ ] erreur nécessitant un rollback
- [ ] Écrire des tests unitaire
- [ ] tester le mode debug et hot reload
- [ ] Tester l'usage de model anyblok comme schéma de validation
- [ ] Permettre la déclaration d'une méthode pour paramétrer des nouvelles routes
- [ ] Permettre la déclaration d'une méthode pour ajouter des middlware starlette

Features
--------

* TODO

Author
------

Pierre Verkest
pierreverkest84@gmail.com
https://github.com/petrus-v

Credits
-------

.. _`Anyblok`: https://github.com/AnyBlok/AnyBlok

This `Anyblok`_ package was created with `audreyr/cookiecutter`_ and the `AnyBlok/cookiecutter-anyblok-project`_ project template.

.. _`AnyBlok/cookiecutter-anyblok-project`: https://github.com/Anyblok/cookiecutter-anyblok-project
.. _`audreyr/cookiecutter`: https://github.com/audreyr/cookiecutter
