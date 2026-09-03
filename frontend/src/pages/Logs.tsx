import { useEffect, useState } from "react";
import api from "../services/api";


interface Log {
    timestamp: string;
    level: string;
    message: string;
}


export default function Logs() {

    const [logs, setLogs] = useState<Log[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");


    const carregarLogs = async () => {

        try {

            const response = await api.get("/logs");

            if (response.data.status === "success") {
                setLogs(response.data.logs);
                setError("");
            } else {
                setError("Não foi possível carregar os logs.");
            }

        } catch (err) {

            console.error("Erro ao carregar logs:", err);
            setError("Erro ao conectar com o Control Room.");

        } finally {

            setLoading(false);

        }
    };


    useEffect(() => {

        carregarLogs();

        // Atualiza os logs automaticamente a cada 5 segundos.
        const intervalo = setInterval(() => {
            carregarLogs();
        }, 5000);

        return () => {
            clearInterval(intervalo);
        };

    }, []);


    return (
        <div>

            <h1>Logs</h1>


            {loading && (
                <p>Carregando logs...</p>
            )}


            {error && (
                <div
                    style={{
                        padding: "12px",
                        marginBottom: "15px",
                        border: "1px solid #dc2626",
                        borderRadius: "6px",
                        color: "#dc2626"
                    }}
                >
                    {error}
                </div>
            )}


            {!loading && !error && (
                <div
                    style={{
                        border: "1px solid #ddd",
                        borderRadius: "8px",
                        overflow: "hidden"
                    }}
                >

                    {logs.length === 0 ? (

                        <div style={{ padding: "20px" }}>
                            Nenhum log encontrado.
                        </div>

                    ) : (

                        logs.map((log, index) => (

                            <div
                                key={index}
                                style={{
                                    padding: "12px 16px",
                                    borderBottom:
                                        index < logs.length - 1
                                            ? "1px solid #eee"
                                            : "none"
                                }}
                            >

                                <div
                                    style={{
                                        display: "flex",
                                        gap: "12px",
                                        marginBottom: "4px"
                                    }}
                                >

                                    <strong>
                                        {log.timestamp}
                                    </strong>

                                    <strong>
                                        [{log.level}]
                                    </strong>

                                </div>


                                <div>
                                    {log.message}
                                </div>

                            </div>

                        ))

                    )}

                </div>
            )}

        </div>
    );
}