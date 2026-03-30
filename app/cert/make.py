from OpenSSL import crypto
import pathlib as ptl
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

class MakeCertificates:
    def __init__(self):
        self.__BASE_DIR = ptl.Path(__file__).parent
        self.pair = crypto.PKey()
        self.pair.generate_key(crypto.TYPE_RSA, 2048)

    def make_public_key(self):
        try:
            public = crypto.dump_publickey(crypto.FILETYPE_PEM, self.pair)
            with open(f"{self.__BASE_DIR}/public.pem", 'wb') as f:
                f.write(public)
            log.info(f"Making public key has been successfuly finished")
        except Exception as e:
            log.info(f"Making public key has been finished with error: {e}")
    def make_private_key(self):
        try:
            private = crypto.dump_privatekey(crypto.FILETYPE_PEM, self.pair)
            with open(f"{self.__BASE_DIR}/private.pem", 'wb') as f:
                f.write(private)
            log.info(f"Making private key has been successfuly finished")
        except Exception as e:
            log.info(f"Making private key has been finished with error: {e}")


if __name__ == "__main__":
    making = MakeCertificates()
    making.make_public_key()
    making.make_private_key()