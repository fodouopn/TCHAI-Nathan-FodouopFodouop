# Exercice1  : Fonction de compression  qui effectue un OU exclusif (XOR) bit à bit de deux expressions de 4 octets chacune

def comp(a, b):
    # Résultat du XOR bit à bit entre a et b (32 bits)
    # XOR bit à bit avec l'opérateur ^ (OU exclusif)
    # Masquage à 32 bits pour s'assurer que le résultat reste sur 4 octets (0xFFFFFFFF)
    return (a ^ b) & 0xFFFFFFFF


# EXERCICE 2 : Fonctions de hachage basées sur le schéma de Merkle-Damgård

# Vecteur d'initialisation IV = 01111000 01100001 01110011 01101000
IV = 0b01111000011000010111001101101000  # 0x78617368

def XD(c):
    """
    Fonction de hachage XD(c) avec rembourrage par zéros.
    Prend une chaîne de caractères et retourne un hash de 4 octets.
    """
    # Convertir la chaîne en bytes
    message_bytes = c.encode('utf-8')
    
    # Rembourrage par zéros : ajouter des zéros jusqu'à ce que la longueur soit un multiple de 4 octets
    message_length = len(message_bytes)
    padding_length = (4 - (message_length % 4)) % 4  # Nombre de zéros à ajouter
    padded_message = message_bytes + b'\x00' * padding_length
    
    # Initialiser avec IV
    h = IV
    
    # Traiter le message par blocs de 4 octets
    for i in range(0, len(padded_message), 4):
        # Extraire un bloc de 4 octets
        bloc = padded_message[i:i+4]
        # Compléter avec des zéros si le dernier bloc est incomplet
        while len(bloc) < 4:
            bloc += b'\x00'
        # Convertir le bloc en entier de 32 bits
        bloc_int = int.from_bytes(bloc, byteorder='big')
        # Appliquer la fonction de compression
        h = comp(h, bloc_int)
    
    return h


def XDD(c):
    """
    Fonction de hachage XDD(c) avec rembourrage par 100...0.
    Prend une chaîne de caractères et retourne un hash de 4 octets.
    """
    # Convertir la chaîne en bytes
    message_bytes = c.encode('utf-8')
    
    # Rembourrage par 100...0 : ajouter un bit 1 puis des zéros
    # On ajoute d'abord 0x80 (10000000 en binaire)
    message_bytes += b'\x80'
    
    # Ajouter des zéros jusqu'à ce que la longueur soit un multiple de 4 octets
    message_length = len(message_bytes)
    padding_length = (4 - (message_length % 4)) % 4
    padded_message = message_bytes + b'\x00' * padding_length
    
    # Initialiser avec IV
    h = IV
    
    # Traiter le message par blocs de 4 octets
    for i in range(0, len(padded_message), 4):
        bloc = padded_message[i:i+4]
        while len(bloc) < 4:
            bloc += b'\x00'
        bloc_int = int.from_bytes(bloc, byteorder='big')
        h = comp(h, bloc_int)
    
    return h


def XDDD(c):
    """
    Fonction de hachage XDDD(c) avec Merkle-Damgård strengthening (100...0 + longueur du message).
    Prend une chaîne de caractères et retourne un hash de 4 octets.
    """
    # Convertir la chaîne en bytes
    message_bytes = c.encode('utf-8')
    original_length = len(message_bytes)  # Longueur originale en octets
    
    # Rembourrage par 100...0 : ajouter 0x80 (bit 1 suivi de zéros)
    message_bytes += b'\x80'
    
    # Calculer la longueur totale nécessaire pour avoir un multiple de 4 octets
    # On doit laisser de la place pour les 4 octets de longueur à la fin
    current_length = len(message_bytes)
    # Ajouter des zéros jusqu'à ce qu'il reste exactement 4 octets pour la longueur
    padding_length = (4 - ((current_length + 4) % 4)) % 4
    padded_message = message_bytes + b'\x00' * padding_length
    
    # Ajouter la longueur du message original (en octets) sur 4 octets
    length_bytes = original_length.to_bytes(4, byteorder='big')
    padded_message += length_bytes
    
    # Initialiser avec IV
    h = IV
    
    # Traiter le message par blocs de 4 octets
    for i in range(0, len(padded_message), 4):
        bloc = padded_message[i:i+4]
        while len(bloc) < 4:
            bloc += b'\x00'
        bloc_int = int.from_bytes(bloc, byteorder='big')
        h = comp(h, bloc_int)
    
    return h


# Exemple d'utilisation
if __name__ == "__main__":
    # Test EXERCICE 1 : Fonction de compression
    print("=== EXERCICE 1 : Fonction de compression ===")
    a = 0x12345678
    b = 0xABCDEF01
    
    resultat = comp(a, b)
    print(f"a = 0x{a:08X}")
    print(f"b = 0x{b:08X}")
    print(f"comp(a, b) = 0x{resultat:08X}")
    print(f"comp(a, b) = {resultat}\n")
    
    # Test EXERCICE 2 : Fonctions de hachage
    print("=== EXERCICE 2 : Fonctions de hachage ===")
    print(f"IV = 0x{IV:08X} = {IV:032b}\n")
    
    # Test avec différentes chaînes
    test_strings = ["hello", "test", "abc", "a", "ABCDEFGHIJKLMNOP"]
    
    for test_str in test_strings:
        print(f"Chaîne d'entrée : '{test_str}'")
        
        # XD(c) - rembourrage par zéros
        hash_XD = XD(test_str)
        print(f"  XD(c)    = 0x{hash_XD:08X} = {hash_XD:032b}")
        
        # XDD(c) - rembourrage par 100...0
        hash_XDD = XDD(test_str)
        print(f"  XDD(c)   = 0x{hash_XDD:08X} = {hash_XDD:032b}")
        
        # XDDD(c) - Merkle-Damgård strengthening
        hash_XDDD = XDDD(test_str)
        print(f"  XDDD(c)  = 0x{hash_XDDD:08X} = {hash_XDDD:032b}")
        print() 