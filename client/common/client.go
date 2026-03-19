package common

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"strings"
	"time"

	"github.com/op/go-logging"
)

func openAgencyFile(id string) (*os.File, error) {

	path := fmt.Sprintf("/dataset/agency-%s.csv", id)

	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}

	return file, nil
}

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	BatchSize     int
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

// en el main del cliente, el tamaño de un vector se hace
// con el batch size
func (c *Client) GetBatchSize() int {
	return c.config.BatchSize
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
// agrego reintentos si justo no arrancó server
func (c *Client) createClientSocket() error {

	var conn net.Conn
	var err error

	for i := 0; i < 10; i++ {

		conn, err = net.Dial("tcp", c.config.ServerAddress)
		if err == nil {
			c.conn = conn
			return nil
		}

		time.Sleep(500 * time.Millisecond)
	}

	log.Criticalf(
		"action: connect | result: fail | client_id: %v | error: %v",
		c.config.ID,
		err,
	)

	return err
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
		"BET|%s,%s,%s,%s,%s,%s\n",
		b.Agency,
		b.FirstName,
		b.LastName,
		b.Document,
		b.BirthDate,
		b.Number,
	)

	return []byte(msg)
}
func serializeBatch(bets []ClientBet) []byte {

	var buffer []byte

	for _, b := range bets {
		buffer = append(buffer, serializeBet(b)...)
	}

	return buffer
}

// a partir de las env var que triggerean a client, genero Bet
func readBetFromCSV(line string, agency string) ClientBet {
	fields := strings.Split(line, ",")

	return ClientBet{
		Agency:    agency,
		FirstName: fields[0],
		LastName:  fields[1],
		Document:  fields[2],
		BirthDate: fields[3],
		Number:    fields[4],
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
	//PARTE 6: Generar un vector de espacio igual al chunk de datos
	//en ese vector se guardan las bets a enviar.
	//seteo las env variables de las compras de usuarios

	//creo un metodo para serializar estos campos en una tira de bytes
	//que pueda enviar por el canal al server

	err := c.createClientSocket()
	if err != nil {
		return
	}

	reader := bufio.NewReader(c.conn)

	file, err := openAgencyFile(c.config.ID)
	if err != nil {
		log.Errorf("action: open_dataset | result: fail | error: %v", err)
		return
	}

	defer file.Close()

	scanner := bufio.NewScanner(file)
	batchSize := c.config.BatchSize
	batch := make([]ClientBet, 0, batchSize)

	for scanner.Scan() {

		line := scanner.Text()

		bet := readBetFromCSV(line, c.config.ID)

		batch = append(batch, bet)

		if len(batch) == batchSize {

			data := serializeBatch(batch)

			err := writeFull(c.conn, data)
			if err != nil {
				c.conn.Close()
				return
			}

			_, err = reader.ReadString('\n')
			if err != nil {
				c.conn.Close()
				return
			}

			for _, b := range batch {
				log.Infof(
					"action: apuesta_enviada | result: success | dni: %s | numero: %s",
					b.Document,
					b.Number,
				)
			}

			batch = batch[:0]
		}
	}

	// flush final
	if len(batch) > 0 {

		data := serializeBatch(batch)

		err := writeFull(c.conn, data)
		if err != nil {
			c.conn.Close()
			return
		}

		_, err = reader.ReadString('\n')
		if err != nil {
			c.conn.Close()
			return
		}

		for _, b := range batch {
			log.Infof(
				"action: apuesta_enviada | result: success | dni: %s | numero: %s",
				b.Document,
				b.Number,
			)
		}
	}
	//comunico que ya no hay mas bets para mandar, quedo en hold
	err = writeFull(c.conn, []byte("END\n"))
	if err != nil {
		c.conn.Close()
		return
	}

	winner_count := 0
	//Segunda etapa, pedimos los resultados
	//abre una segunda conexión por que el server solo maneja un socket a la vez
	//asi que para que trabaje con todos los clients, tiene que cerrar las conns

	for {
		err = c.createClientSocket()
		if err != nil {
			return
		}
		err = writeFull(c.conn, []byte("GET\n"))
		if err != nil {
			return
		}

		reader = bufio.NewReader(c.conn)
		line, err := reader.ReadString('\n')
		if err != nil {
			c.conn.Close()
			return
		}

		line = strings.TrimSpace(line)

		//si no terminaron de mandar los bets otros clients, voy a esperar y
		//volver a preguntar en unt iempo
		if line == "WAIT" {
			c.conn.Close()
			time.Sleep(500 * time.Millisecond)
			continue
		}

		winner_count := 0
		for {
			if strings.HasPrefix(line, "WIN|") {
				winner_count++
			} else if line == "END" {
				break
			}
			line, err = reader.ReadString('\n')
			if err != nil {
				break
			}
			line = strings.TrimSpace(line)
		}
		c.conn.Close()

		log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %v", winner_count)
		break
	}

	log.Infof(
		"action: consulta_ganadores | result: success | cant_ganadores: %v", winner_count,
	)

	c.conn.Close()

	log.Infof(
		"action: loop_finished | result: success | client_id: %v",
		c.config.ID,
	)
	//PARTE 6: se debería cambiar a iterar el vector de bets e ir enviandolas
	//con los metos de serialize y write full que ya existen

	//Parte 6: se van a ir mandando bets de a chunks.
	//cuando terminas con el ultimo chunk, ahí si cerras conexion

	//este loop medio que se iría si ahora client solo se encarga de comunicar
	//bets a server, no habría mas msgId

}
