import os
os.environ['APCA_API_BASE_URL'] = 'https://paper-api.alpaca.markets'
os.environ['APCA_API_KEY_ID'] = 'PKVQCPLCNIT0LP3PCG01'
os.environ['APCA_API_SECRET_KEY'] = '24F86p4D6CjNw0YEL4ZtcoiTpeSepcJxXccfsZH5'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:/Users/Mohit/PycharmProjects/SuperAIPR/newslstmstockbot/keys.json'
varvar = 0
while True:
    print('Loop has been completed', varvar,'time(s)')
    os.system('python train.py')
