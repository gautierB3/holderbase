.. holderbase documentation master file, created by
   sphinx-quickstart on Mon Sep 11 10:17:40 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to holderbase's documentation!
======================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules/holderbase
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Assumptions
===========

File upload
-----------

- There is currently only one version of the uploaded file.
- One full file is processed at this stage. 
- The system accepts csv extensions.
- Files received are simply stored in the file system using the MD5 hash of the file as name. The hash is stored in party table as "Last uploaded file".
- File is treated only if sender is known. 
- File must include the sender information as well as the timestamp of data when produced.

File Data
---------

- Record types:
    - 100: sender info
    - 200: upstream holding
    - 300: downstream legal entity holding
    - 350: downstream private holding
    - 400: downstream self holding
    - 800: upstream holding from issuer
    - 900: issuer information 
    
- Roles:
    - CUS: for "Custodians" Custodians and Intermediaries
    - CSD: for "Central Securities Depository"
    - ISS: for "Issuer"
    - OWN: for "Beneficial Owner"
    
- ISIN: For "International Security Identification Number". A 12-character alphanumeric code.
- LEI: For "Legal Entity Identifier". A 20-character alphanumeric code.
- Country: The ISO 3166-1 country reference.
- Timestamp: The client processed batch time (epoch format).

Database
--------

- The "Party" table:
    - can only have one company type, namely; Issuer, CSD, Custodian, Holder, or Owner.
    - The country reference is based on  ISO 3166-1.
    - Created and updated are based on database creation and update.
    
- The "Security" table:
    - ISIN is required, cannot be blank
    - Issuer and depository are (currently) not required.
    - securities can only have one issuer (many-to-one relationship) and is therefore related to the party table simply as a foreign key.
    - securites can only have one depository (many-to-one relationship) and is therefore related to the party table simply as a foreign key.
    - Foreign key behavior is set to protect the security table, consequently it will not be possible to delete a party if there are existing securities related to it (via Issuer or depository).
    - Created and updated are based on database creation and update
    
- The "Holding" table:
    - Party_from, party_to and related security are required.
    - Foreign keys are cascading on delete: deleting a party or a security will delete all related edges.
    - Created and updated are based on batch timestamp from files.