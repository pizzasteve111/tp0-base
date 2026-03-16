package common

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// si llame a sigterm, que se asegure cerrar la conn
func (c *Client) HandleShutdown() {
	if c.conn != nil {
		c.conn.Close()
	}
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

type ClientBet struct {
	Agency    string
	FirstName string
	LastName  string
	Document  string
	BirthDate string
	Number    string
}

// devuelve una tira de bytes que puedo pasar por canal
func serializeBet(b ClientBet) []byte {
	msg := fmt.Sprintf(
		"%s,%s,%s,%s,%s,%s\n",
		b.Agency,
		b.FirstName,
		b.LastName,
		b.Document,
		b.BirthDate,
		b.Number,
	)

	return []byte(msg)
}

// a partir de las env var que triggerean a client, genero Bet
func readBetFromEnv(clientID string) ClientBet {
	return ClientBet{
		Agency:    clientID,
		FirstName: os.Getenv("NOMBRE"),
		LastName:  os.Getenv("APELLIDO"),
		Document:  os.Getenv("DOCUMENTO"),
		BirthDate: os.Getenv("NACIMIENTO"),
		Number:    os.Getenv("NUMERO"),
	}
}
func writeFull(conn net.Conn, data []byte) error {

	total := 0

	for total < len(data) {

		n, err := conn.Write(data[total:])
		if err != nil {
			return err
		}

		total += n
	}

	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	//seteo las env variables de las compras de usuarios
	bet := readBetFromEnv(c.config.ID)
	//creo un metodo para serializar estos campos en una tira de bytes
	//que pueda enviar por el canal al server

	err := c.createClientSocket()
	if err != nil {
		return
	}

	data := serializeBet(bet)

	err = writeFull(c.conn, data)
	if err != nil {

		c.conn.Close()
		return
	}

	reader := bufio.NewReader(c.conn)
	_, err = reader.ReadString('\n')
	c.conn.Close()

	if err != nil {
		return
	}

	log.Infof(
		"action: apuesta_enviada | result: success | dni: %s | numero: %s",
		bet.Document,
		bet.Number,
	)

	//este loop medio que se iría si ahora client solo se encarga de comunicar
	//bets a server, no habría mas msgId

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
