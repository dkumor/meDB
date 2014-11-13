"""
The Outputs data structure is as follows:

_id: randomly generated identifier
parent: The uid of the parent
output: The SINGLE output from the database - all "outputs" within here are linked, meaning that they correspond
        to something like a "query". Each independent output should be independently registered. For example,
        3 light switches correspond to 3 separate output objects. But say an email would correspond of a title and body
        at the same time.
        {
            partname: {metadata}
        }
meta: {metadata} All metadata associated with the output - such as perhaps a human-readable name, and so forth
"""
import uuid
from bson.objectid import ObjectId
