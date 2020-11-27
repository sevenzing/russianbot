def pluralForm(n, form1, form2, form5):
    '''

    :param form1: 'письмо'
    :param form2: 'письма'
    :param form5: 'писем'
    :return:
    '''
    n = abs(n) % 100
    n1 = n % 10
    if n > 10 and n < 20:
        return form5
    if n1 > 1 and n1 < 5:
        return form2
    if n1 == 1:
        return form1

    return form5


