class PvToken:

    def __init__(self, token_id, token_value):
        """
        :param token_id:
        :type token_id: int
        :param token_value: token value
        :type token_value: str
        """
        self.id = token_id
        self.value = token_value

    def __str__(self):
        return 'Token(' + str(self.id) + ',' + str(self.value) + ')'

    def get_id(self):
        """
        Return the token id
        :return: token id
        :rtype: int
        """
        return self.id

    def get_value(self):
        """
        Return the token value
        :return: token value
        :rtype: str
        """
        return str(self.value)

    def match(self, token_id):
        """
        Check whether a token has a certain id
        :param token_id: token id
        :type token_id: int
        :return true if token id matches the specified id
        :rtype: bool
        """
        return True if self.id == token_id else False

    def is_in(self, token_id_list):
        """
        Check whether a token id is in a list of possible id's
        :param token_id_list: list of token id's
        :type token_id_list: list
        :return: true if the token id is in the list
        :rtype: bool
        """
        return True if self.id in token_id_list else False


if __name__ == '__main__':
    t1 = PvToken(1, "23")
    t2 = PvToken(2, "abc")
    t3 = PvToken(1, "hello")
    print(t1 == t2)
    print(t1 == t3)
    print(t2.match(2))
    print(t2.match(4))
