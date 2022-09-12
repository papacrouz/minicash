from app.utils.serutil import (
    ser_str, 
    deser_str
)

import io




def proof_serialize(proof, out_type=None):
    f = io.BytesIO()
    # serialize proof 
    f.write(ser_str(str(proof["C"]["x"]).encode()))
    f.write(ser_str(str(proof["C"]["y"]).encode()))
    f.write(ser_str(str(proof["amount"]).encode()))
    f.write(ser_str(str(proof["public_key"]).encode()))

    if not out_type:
        return f.getvalue()
    elif out_type == "hex":
        return f.getvalue().hex()



def proof_deserialize(proof):
    f = io.BytesIO(proof)
    # deserialize proof 
    x = deser_str(f)
    y = deser_str(f)
    amount = deser_str(f)
    secret = deser_str(f)
    # construct 
    proof = {'amount': int(amount), 'C': {'x': int(x), 'y': int(y)}, 'public_key': secret.decode()}
    return proof