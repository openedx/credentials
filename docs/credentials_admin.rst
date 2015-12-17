======================
Site Configuration
======================

This is a custom functionality to add site-specific configuration.
We have extended the `Django sites framework <https://docs.djangoproject.com/en/1.8/ref/contrib/sites/>`_ in order to add this configuration.
The site's framework allows for the mapping of domains to a **Site** object which consists of an ID and a name.

The multi-tenant implementation has one site per configuration.


---------------------------------------------
Site Configuration Model | Django Admin
---------------------------------------------

To add and update a custom site's configurations, including the basic theming, use the ``SiteConfiguration`` model.

The following image shows the ``SiteConfiguration`` model in the Django administration panel for a configured site.

.. image:: _static/images/site_configuration.png
    :width: 600px
    :alt: Populated site configuration model

.. note::  All the fields in ``SiteConfiguration`` model are **require** and can not be **Null**.

    Please make sure that there is only one site configuration per site.


=========================
Template Configuration
=========================

This is a configuration to add certificate-specific template.
This is not a required configuration as if there is no certificate specific template added then default template would be used to render Certificate.


-----------------------------------------------
Template Configuration Model | Django Admin
-----------------------------------------------

To add and update template's configuration use the ``CertificateTemplate`` model.

The following image shows the ``CertificateTemplate`` model in Django administration panel for a configured template.

.. image:: _static/images/template.png
    :width: 600px
    :alt: Populated template model

.. note::  All the fields in ``CertificateTemplate`` model are **require** and can not be **null**.


-------------------------------------------
Template Asset Model | Django Admin
-------------------------------------------

``CertificateTemplateAsset`` model will be use to upload templates on the S3 bucket. These assets could be use in the **content** of the ``CertificateTemplate`` model.

The following image shows the ``CertificateTemplateAsset`` model in Django administration panel for a configured certificate template asset.

.. image:: _static/images/template_asset.png
    :width: 600px
    :alt: Populated template asset model

.. note::  All the fields in ``CertificateTemplate`` model are **require** and can not be **null**.


==========================
Signatory Configuration
==========================

This is the configuration to add signatories for the certificate.
This is a required configuration as every certificate must have the signature for approval.

------------------------------------------------
Signatory Configuration Model | Django Admin
------------------------------------------------

To add and update signatory's configuration use the ``Signatory`` model.

The following image shows the ``Signatory`` model in Django administration panel for a configured signatory.

.. image:: _static/images/signatory.png
    :width: 600px
    :alt: Populated signatory model

.. note::  All the fields in ``Signatory`` model are **require** and can not be **null**.



====================================
Course Certificate Configuration
====================================

This is the configuration to add course certificates.
This configuration creates a new **CourseCertificate** object that will be use to award course certificates to learners.

--------------------------------------------------------
Course Certificate Configuration Model | Django Admin
--------------------------------------------------------

To add and update course certificate's configuration use the ``CourseCertificate`` model.

The following image shows the ``CourseCertificate`` model in Django administration panel for a configured course certificate.

.. image:: _static/images/course_certificate.png
    :width: 600px
    :alt: Populated course certificate model

.. note::  There is a **unique together** constraint on the **site** , **Course id** and **Certificate type** fields for the ``CourseCertificate`` model.
    This means there can not be more than one entry for the same site, course id and certificate type.


====================================
Program Certificate Configuration
====================================

This is the configuration to add program certificates.
This configuration creates a new **ProgramCertificate** object that will be use to award program certificates to learners.

----------------------------------------------------------
Program Certificate Configuration Model | Django Admin
----------------------------------------------------------

To add and update program certificate's configuration use the ``ProgramCertificate`` model.

The following image shows the ``ProgramCertificate`` model in Django administration panel for a configured program certificate.

.. image:: _static/images/program_certificate.png
    :width: 600px
    :alt: Populated program certificate model
