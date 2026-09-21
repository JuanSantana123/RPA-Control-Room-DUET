import { useCallback, useEffect, useRef, useState } from "react";


// ============================================================
// TIPOS
// ============================================================

export type TerminalStatus =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error";


interface UseRobotStudioTerminalParams {
  // Projeto atualmente aberto no Studio.
  projectId: number;

  // Controla se o terminal deve permanecer conectado.
  enabled: boolean;

  // Recebe os dados enviados pelo backend.
  onData: (data: string) => void;
}


// ============================================================
// MONTAR URL DO WEBSOCKET
// ============================================================

function buildTerminalWebSocketUrl(
  projectId: number,
): string {

  /*
   * O frontend do DUET roda no Vite (porta 5173),
   * enquanto o Control Room/FastAPI roda na porta 9000.
   *
   * O WebSocket pertence ao Control Room, portanto precisa
   * conectar no backend e não no servidor do frontend.
   *
   * IMPORTANTE:
   * Esta configuração acompanha o endereço atualmente usado
   * pelo cliente Axios em services/api.ts.
   */
  const controlRoomUrl =
    "http://localhost:9000";

  /*
   * Converte o protocolo HTTP da API para o protocolo
   * correspondente de WebSocket:
   *
   * http://  -> ws://
   * https:// -> wss://
   */
  const websocketBaseUrl =
    controlRoomUrl.replace(
      /^http/,
      "ws",
    );

  return (
    `${websocketBaseUrl}` +
    `/development/projects/${projectId}/terminal`
  );
}
// ============================================================
// HOOK DO TERMINAL
// ============================================================

export function useRobotStudioTerminal({
  projectId,
  enabled,
  onData,
}: UseRobotStudioTerminalParams) {

  const socketRef =
    useRef<WebSocket | null>(null);

  /*
   * Mantém a versão mais recente do callback sem obrigar
   * a conexão WebSocket a ser recriada a cada render.
   */
  const onDataRef =
    useRef(onData);

  const [status, setStatus] =
    useState<TerminalStatus>("disconnected");


  // ==========================================================
  // ATUALIZAR CALLBACK
  // ==========================================================

  useEffect(() => {

    onDataRef.current = onData;

  }, [onData]);


  // ==========================================================
  // CONECTAR
  // ==========================================================

  useEffect(() => {

    if (!enabled || !projectId) {

      setStatus("disconnected");

      return;
    }


    setStatus("connecting");

    const socket = new WebSocket(
      buildTerminalWebSocketUrl(projectId),
    );

    socketRef.current = socket;


    // --------------------------------------------------------
    // CONEXÃO ABERTA
    // --------------------------------------------------------

    socket.onopen = () => {

      setStatus("connected");

    };


    // --------------------------------------------------------
    // DADOS RECEBIDOS DO CMD.EXE
    // --------------------------------------------------------

    socket.onmessage = (event) => {

      if (typeof event.data === "string") {

        onDataRef.current(event.data);

      }

    };


    // --------------------------------------------------------
    // ERRO
    // --------------------------------------------------------

    socket.onerror = () => {

      setStatus("error");

    };


    // --------------------------------------------------------
    // CONEXÃO ENCERRADA
    // --------------------------------------------------------

    socket.onclose = () => {

      if (socketRef.current === socket) {

        socketRef.current = null;

      }

      setStatus("disconnected");

    };


    // --------------------------------------------------------
    // CLEANUP
    // --------------------------------------------------------

    return () => {

      socket.onopen = null;
      socket.onmessage = null;
      socket.onerror = null;
      socket.onclose = null;

      if (
        socket.readyState === WebSocket.OPEN ||
        socket.readyState === WebSocket.CONNECTING
      ) {

        socket.close();

      }

      if (socketRef.current === socket) {

        socketRef.current = null;

      }

    };

  }, [projectId, enabled]);


  // ==========================================================
  // ENVIAR INPUT
  // ==========================================================
    // ==========================================================
  // ENVIAR INPUT
  // ==========================================================

  const send = useCallback(
    (data: string) => {

      const socket = socketRef.current;

      if (
        !socket ||
        socket.readyState !== WebSocket.OPEN
      ) {

        return false;

      }


      /*
       * O WebSocket do terminal utiliza mensagens estruturadas.
       *
       * INPUT:
       * representa exatamente os caracteres produzidos pelo xterm.
       *
       * Exemplos:
       * - letras;
       * - Enter;
       * - Backspace;
       * - sequências de controle.
       */
      socket.send(
        JSON.stringify({
          type: "input",
          data,
        }),
      );

      return true;

    },
    [],
  );


  // ==========================================================
  // REDIMENSIONAR TERMINAL
  // ==========================================================

  const resize = useCallback(
    (
      rows: number,
      cols: number,
    ) => {

      const socket = socketRef.current;

      if (
        !socket ||
        socket.readyState !== WebSocket.OPEN
      ) {

        return false;

      }


      /*
       * Informa ao ConPTY o tamanho calculado pelo xterm.
       *
       * Isso mantém:
       *
       * - cursor;
       * - quebra de linha;
       * - prompt;
       * - aplicações interativas
       *
       * sincronizados com o terminal exibido no Studio.
       */
      socket.send(
        JSON.stringify({
          type: "resize",
          rows,
          cols,
        }),
      );

      return true;

    },
    [],
  );

  return {
    status,
    send,
    resize,
  };
}