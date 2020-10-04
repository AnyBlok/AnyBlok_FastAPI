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
- [x] Tester l'usage de model anyblok comme schéma de validation => ne fonctionne pas directement, nécessite probablement la création d'un nouveau type ?
- [x] Tester l'intégration gunicorn
- [ ] Écrire des tests unitaire
- [ ] Gestion des exceptions (https://fastapi.tiangolo.com/tutorial/handling-errors/):
    - [ ] erreur de validation
    - [ ] erreur SQLA genre un enregistrement non trouvé avec un one
    - [ ] erreur nécessitant un rollback
- [ ] tester le mode debug et hot reload
- [ ] Permettre la déclaration d'un nouveau type Schema, qui permettra la surcharge dynamique et à chaud des blocks
- [ ] Permettre la déclaration d'une méthode pour paramétrer des nouvelles routes au niveau du package python
- [ ] Permettre la déclaration d'une méthode pour ajouter des middlware starlette au niveau du package python

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
