from preprocessing import data_loader
from model import CNN
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from preprocessing import AlexEmbed
from torch.utils.data import DataLoader
alexembed = AlexEmbed()


def loaders(dataset, split = 0.8, batch_size = 256):

    train_size = int(split * len(dataset))
    val_size = len(dataset) - train_size
    train_set, val_set = torch.utils.data.random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size, shuffle=True)
    val_loader = DataLoader(val_set, 1024, shuffle=True)
    return train_loader, val_loader

def train(net, train_loader, val_loader, batch_size=64, lr=0.001, num_epochs=30):
    # Fixed PyTorch random seed for reproducible result
    torch.manual_seed(0)

    if torch.cuda.is_available():
        net = net.cuda()

    # cross entropy loss function and adaptive moment estimation optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(net.parameters(), lr = lr, weight_decay=0.1)

    # softmax for predictions
    softmax = nn.Softmax(dim = 1)
    
    # initialize error and loss history
    train_err = np.zeros(num_epochs)
    train_loss = np.zeros(num_epochs)
    val_err = np.zeros(num_epochs)
    val_loss = np.zeros(num_epochs)
    
    for epoch in tqdm(range(num_epochs)):
        total_train_loss = 0.0
        total_train_err = 0.0
        train_iters = 0

        total_val_loss = 0.0
        total_val_err = 0.0
        val_iters = 0
        
        train_batches = 0
        net.train()
        for batch in train_loader:
            train_batches += 1
            imgs, labels = batch.values()
            if torch.cuda.is_available():
                imgs = imgs.cuda()
                labels = labels.cuda()
            optimizer.zero_grad()
            outputs = net(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            pred = softmax(outputs)
            #print("debug1", pred.shape, labels.shape)
            # find error and loss for training data
            #total_train_err += (np.argmax(pred.detach().cpu(), 1) != np.argmax(labels.cpu(), 1)).sum().item()
            total_train_err += (np.argmax(pred.detach().cpu(), 1) != labels.cpu()).sum().item()
            total_train_loss += loss.item()
            train_iters += len(labels)

        val_batches = 0
        net.eval()
        for batch in val_loader:
            val_batches += 1
            imgs, labels = batch.values()
            if torch.cuda.is_available():
                imgs = imgs.cuda()
                labels = labels.cuda()
            outputs = net(imgs)
            loss = criterion(outputs, labels)

            pred = softmax(outputs)

            # find error and loss for training data
            total_val_err += (np.argmax(pred.detach().cpu(), 1) != labels.cpu()).sum().item()
            total_val_loss += loss.item()
            val_iters += len(labels)

        # record the average error (per iteration) and loss (per batch) for each epoch
        train_err[epoch] = total_train_err / train_iters
        train_loss[epoch] = total_train_loss / train_batches
        val_err[epoch] = total_val_err / val_iters
        val_loss[epoch] = total_val_loss / val_batches
        print(f"Epoch {epoch}: Train err: {train_err[epoch]} Val err: {val_err[epoch]} Train loss: {train_loss[epoch]} Val loss: {val_loss[epoch]}")
        # save model
        model_path = "bs{}_lr{}_epoch{}".format(batch_size,
                                              lr,
                                              epoch)
        torch.save(net.state_dict(), model_path)
    return train_err, train_loss, val_err, val_loss

def evaluation(net, batch_size=1024): # Evaluate the error/loss of a loaded model
    # Fixed PyTorch random seed for reproducible result
    torch.manual_seed(0)

    if torch.cuda.is_available():
        #print("cuda activated")
        net = net.to('cuda')

    train_loader, val_loader = data_loader(batch_size=batch_size)
    
    # cross entropy loss function
    criterion = nn.CrossEntropyLoss()

    # softmax for predictions
    softmax = nn.Softmax(dim = 1)
    
    # initialize error and loss history
    total_train_loss = 0.0
    total_train_err = 0.0
    train_iters = 0

    total_val_loss = 0.0
    total_val_err = 0.0
    val_iters = 0

    train_batches = 0
    net.eval()
    for batch in tqdm(train_loader):
        train_batches += 1
        imgs, labels = batch.values()
        if torch.cuda.is_available():
            imgs = imgs.to('cuda')
            labels = labels.to('cuda')
        outputs = net(imgs)
        loss = criterion(outputs, labels)

        pred = softmax(outputs)
        # find error and loss for training data
        total_train_err += (np.argmax(pred.detach().cpu(), 1) != np.argmax(labels.cpu(), 1)).sum().item()
        print(total_train_err)
        total_train_loss += loss.item()
        train_iters += len(labels)

    val_batches = 0
    for batch in tqdm(val_loader):
        val_batches += 1
        imgs, labels = batch.values()
        if torch.cuda.is_available():
            imgs = imgs.to('cuda')
            labels = labels.to('cuda')
        outputs = net(imgs)
        loss = criterion(outputs, labels)

        pred = softmax(outputs)

        # find error and loss for training data
        total_val_err += (np.argmax(pred.detach().cpu(), 1) != np.argmax(labels.cpu(), 1)).sum().item()
        total_val_loss += loss.item()
        val_iters += len(labels)

    return total_train_loss, total_train_err/len(train_loader), total_val_loss, total_val_err/len(val_loader)


def plot(train_err, train_loss, val_err, val_loss):
    n = len(train_err) # number of epochs

    fig, (ax1, ax2) = plt.subplots(1, 2)
    ax1.set_title("Train vs Validation Error")
    ax1.plot(range(1,n+1), train_err, label="Train")
    ax1.plot(range(1,n+1), val_err, label="Validation")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Error")
    ax1.legend(loc='best')
    ax1.xaxis.get_major_locator().set_params(integer=True)
    ax2.set_title("Train vs Validation Loss")
    ax2.plot(range(1,n+1), train_loss, label="Train")
    ax2.plot(range(1,n+1), val_loss, label="Validation")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Loss")
    ax2.legend(loc='best')
    ax2.xaxis.get_major_locator().set_params(integer=True)
    plt.show()

def performance_per_class(net):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    
    net = net.to(device)
    net.eval()
    _, val_loader = data_loader(batch_size=1)

    
    errors = {
        0:0,
        1:0,
        2:0,
        3:0,
        4:0,
        5:0,
        6:0,
        7:0,
        8:0,
        9:0,
        10:0,
        11:0,
        12:0,
        13:0,
        14:0,
    }
    total = {
        0:0,
        1:0,
        2:0,
        3:0,
        4:0,
        5:0,
        6:0,
        7:0,
        8:0,
        9:0,
        10:0,
        11:0,
        12:0,
        13:0,
        14:0,
    }
    wrong_guesses = {
        0:0,
        1:0,
        2:0,
        3:0,
        4:0,
        5:0,
        6:0,
        7:0,
        8:0,
        9:0,
        10:0,
        11:0,
        12:0,
        13:0,
        14:0,
    }
    guesses = {
        0:0,
        1:0,
        2:0,
        3:0,
        4:0,
        5:0,
        6:0,
        7:0,
        8:0,
        9:0,
        10:0,
        11:0,
        12:0,
        13:0,
        14:0,
    }
    
    
    softmax = nn.Softmax(dim = 1)
    for batch in val_loader:
        img, label = batch.values()
        if torch.cuda.is_available():
                img = img.to('cuda')
                label = label.to('cuda')
        
        

        output = softmax(net(img))

        pred = np.argmax(output.detach().cpu()).item()
        #print(pred)
        truth = np.argmax(label.cpu()).item()
        if pred != truth:
            errors[truth] += 1
            wrong_guesses[pred] += 1
        total[truth] += 1
        guesses[pred] += 1
    for i in range(15):
        if guesses[i] == 0:
            wrong_guesses[i] = guesses[i]
        else: 
            wrong_guesses[i] /= guesses[i]
        if total[i] == 0:
            errors[i] = 0
        else:
            errors[i] /= total[i]
    return errors, wrong_guesses, guesses

if __name__ == "__main__":
    # net = Baseline()
    # train_err, train_loss, val_err, val_loss = train(net, 64, 0.001, 20)
    # plot(train_err, train_loss, val_err, val_loss)
    #net = CNN()
    #net.load_state_dict(torch.load("./models/bs256_lr0.0001_epoch29", map_location=torch.device('cpu')))
    #print(net)
    #train_err, train_loss, val_err, val_loss = train(net, 128, 0.0001, 29)
    #error_rate, wrong_guess_rate, guesses = performance_per_class(net)
    # print("The error rate is:"+ str(error_rate))
    # print(wrong_guess_rate)
    # print(guesses)

    x = np.array([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14])
    xtick = ["sitting", "using_laptop", "hugging", "sleeping", "drinking", "clapping", "dancing", "cycling",
     "calling", "laughing", "eating", "fighting", "listening_to_music", "running", "texting"]
    
    plt.xticks(x, xtick, rotation=45)
    plt.plot(x, error_rate.values())
    plt.title("Error rates per class")
    plt.xlabel("Class")
    plt.ylabel("Error rate")
    plt.show()
    plt.xticks(x, xtick, rotation=45)
    plt.plot(x, wrong_guess_rate.values())
    plt.title("Wrong guess rate per class")
    plt.xlabel("Class")
    plt.ylabel("Wrong guess rate")
    plt.show()
    plt.xticks(x, xtick, rotation=45)
    plt.plot(x, guesses.values())
    plt.title("Guesses per class")
    plt.xlabel("Class")
    plt.ylabel("Number of guesses")
    plt.show()
    #from torchinfo import summary
    #summary(net, input_size=(256, 3, 224, 224))
