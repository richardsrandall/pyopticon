
// This is a sketch that you can load onto an Arduino to make digital pin 5 
// controllable by a RichardView IoT relay widget. Pin 5 can then control a
// Digital Loggers IoT relay.

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(5, OUTPUT);
  digitalWrite(5,LOW);
}

const int MaxChars = 10; // an int string contains up to 5 digits and
                        // is terminated by a 0 to indicate end of string
char strValue[MaxChars+1]; // must be big enough for digits and terminating null
int index = 0;         // the index into the array storing the received digits

String status="0";

void processCommand(char* command) {
  String cmd = command;

  if(cmd.equals("1")){ // Turn on
    digitalWrite(5,HIGH);
    status="1";

  } else if (cmd.equals("0")) { // Turn off
    digitalWrite(5,LOW);
    status="0";
  } else if (command[0]=='Q') { // Query status
    Serial.println(status);
  }
}

void loop() {

    if( Serial.available())
    {
      char ch = Serial.read();
      if(index <  MaxChars && ch !=13 && ch !=10){//Not newline or carriage return
        strValue[index++] = ch; // add the ASCII character to the string;
      }
      else
      {
        // here when buffer full or on the first newline/carriage return
        strValue[index] = 0;        // terminate the string with a 0
        index = 0;
        processCommand(strValue);
      }
    }
}
