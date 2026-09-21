import {
  useCallback,
  useEffect,
  useRef,
} from "react";

import {
  Terminal as XTerm,
} from "@xterm/xterm";

import {
  FitAddon,
} from "@xterm/addon-fit";

import "@xterm/xterm/css/xterm.css";

import {
  useRobotStudioTerminal,
} from "../../hooks/robot-studio/useRobotStudioTerminal";

import "./RobotStudioTerminal.css";


// ============================================================
// PROPS
// ============================================================

interface RobotStudioTerminalProps {
  projectId: number;

  /*
   * O terminal só deve existir quando o usuário puder alterar
   * o Workspace. Isso acompanha a regra de Checkout do Studio.
   */
  enabled: boolean;
}


// ============================================================
// COMPONENTE
// ============================================================

export default function RobotStudioTerminal({
  projectId,
  enabled,
}: RobotStudioTerminalProps) {

  const containerRef =
    useRef<HTMLDivElement | null>(null);

  const terminalRef =
    useRef<XTerm | null>(null);

  const fitAddonRef =
    useRef<FitAddon | null>(null);


  // ==========================================================
  // RECEBER OUTPUT DO BACKEND
  // ==========================================================

  const handleTerminalData =
    useCallback((data: string) => {

      terminalRef.current?.write(data);

    }, []);


  // ==========================================================
  // WEBSOCKET
  // ==========================================================

  const {
    status,
    send,
    resize,
  } = useRobotStudioTerminal({
    projectId,
    enabled,
    onData: handleTerminalData,
  });


  // ==========================================================
  // CRIAR XTERM
  // ==========================================================

  useEffect(() => {

    const container =
      containerRef.current;

    if (!container) {
      return;
    }


    const terminal = new XTerm({

      /*
       * Aparência semelhante a terminais modernos.
       * Não definimos tema manualmente aqui para evitar
       * duplicar os tokens visuais do Studio.
       */
      cursorBlink: true,

      fontFamily:
        'Consolas, "Courier New", monospace',

      fontSize: 13,

      lineHeight: 1.2,

      scrollback: 5000,

      convertEol: true,

    });


    const fitAddon =
      new FitAddon();


    terminal.loadAddon(
      fitAddon,
    );


    terminal.open(
      container,
    );


    /*
     * Registra primeiro a instância ativa.
     *
     * Assim qualquer evento de foco/click executado depois da
     * montagem já encontra o terminal correto.
     */
    terminalRef.current =
      terminal;

    fitAddonRef.current =
      fitAddon;


    /*
     * O xterm recebe entrada de teclado através de um textarea
     * interno criado por terminal.open().
     *
     * O foco precisa acontecer depois que esse elemento já foi
     * efetivamente inserido no DOM.
     */
    requestAnimationFrame(() => {

      terminal.focus();

    });


    // --------------------------------------------------------
    // INPUT DO DESENVOLVEDOR
    // --------------------------------------------------------

    const inputDisposable =
      terminal.onData((data) => {
        /*
         * Encaminha os caracteres produzidos pelo xterm para
         * o pseudoterminal Windows através do WebSocket.
         */

          send(data);


      });


    // --------------------------------------------------------
    // AJUSTAR TAMANHO INICIAL
    // --------------------------------------------------------

    requestAnimationFrame(() => {

      try {

        fitAddon.fit();
        /*
         * Depois do FitAddon calcular o tamanho visual real,
         * sincronizamos essas dimensões com o ConPTY.
         */
        resize(
          terminal.rows,
          terminal.cols,
        );

      } catch {

        // O container pode ainda não possuir dimensões
        // durante a montagem inicial.

      }

    });


    // --------------------------------------------------------
    // RESIZE
    // --------------------------------------------------------

    const resizeObserver =
      new ResizeObserver(() => {

        try {

          fitAddon.fit();
          /*
          * Depois do FitAddon calcular o tamanho visual real,
          * sincronizamos essas dimensões com o ConPTY.
          */
          resize(
            terminal.rows,
            terminal.cols,
          );

        } catch {

          // Ignora resize enquanto o elemento estiver oculto.

        }

      });


    resizeObserver.observe(
      container,
    );


    // --------------------------------------------------------
    // CLEANUP
    // --------------------------------------------------------

    return () => {

      resizeObserver.disconnect();

      inputDisposable.dispose();

      terminal.dispose();

      terminalRef.current = null;
      fitAddonRef.current = null;

    };

  }, [send, resize, enabled]);



  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div className="studio-terminal">

      <div className="studio-terminal__header">

        <span>
          TERMINAL
        </span>

        <span
          className={
            `studio-terminal__status ` +
            `studio-terminal__status--${status}`
          }
        >
          {status === "connected"
            ? "Conectado"
            : status === "connecting"
              ? "Conectando..."
              : status === "error"
                ? "Erro"
                : "Desconectado"}
        </span>

      </div>


      {!enabled ? (

        <div className="studio-terminal__disabled">

          Faça Checkout do projeto para utilizar o terminal.

        </div>

      ) : (

        <div
          ref={containerRef}
          className="studio-terminal__xterm"

          /*
           * O xterm utiliza um textarea interno invisível para
           * capturar o teclado.
           *
           * Usamos onClick em vez de onMouseDown para deixar o
           * processamento normal do mouse terminar antes de
           * devolver o foco ao terminal.
           */
          onClick={() => {

            const terminal =
              terminalRef.current;

            if (!terminal) {
              return;
            }

            terminal.focus();

          }}
        />

      )}

    </div>
  );
}