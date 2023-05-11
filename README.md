# Python Substack

# Introduction

This is an unofficial library providing a Python interface for [Substack](https://substack.com/).
I am in no way affiliated with Substack. It works with
Python versions from 3.7+.

# Installation

You can install python-substack using:

    $ pip install python-substack

# Usage

Set the following environment variables by creating a **.env** file:

    PUBLICATION_URL=https://ma2za.substack.com
    EMAIL=
    PASSWORD=
    USER_ID=

The only way I found to discover the USER_ID is to inspect
the payload to a **/drafts** request. Under the fields **draftBylines**
or **postBylines** there is a subfield **user_id** or **id**

The .env file will be ignored by git but always be careful.