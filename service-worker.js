import React, { useState } from "react";
import { View, Text, TextInput, Button, StyleSheet } from "react-native";

export default function App() {
    const [balance, setBalance] = useState("");
    const [risk, setRisk] = useState("");
    const [stopLoss, setStopLoss] = useState("");
    const [lotSize, setLotSize] = useState(null);

    const calculateLotSize = () => {
        const riskAmount = (parseFloat(balance) * parseFloat(risk)) / 100;
        const size = riskAmount / parseFloat(stopLoss);
        setLotSize(size.toFixed(2));
    };

    return (
        <View style={styles.container}>
            <Text style={styles.header}>Forex Lot Size Calculator</Text>
            <TextInput placeholder="Account Balance ($)" keyboardType="numeric" value={balance} onChangeText={setBalance} style={styles.input} />
            <TextInput placeholder="Risk Percentage (%)" keyboardType="numeric" value={risk} onChangeText={setRisk} style={styles.input} />
            <TextInput placeholder="Stop Loss (pips)" keyboardType="numeric" value={stopLoss} onChangeText={setStopLoss} style={styles.input} />
            <Button title="Calculate" onPress={calculateLotSize} />
            {lotSize && <Text style={styles.result}>Lot Size: {lotSize} lots</Text>}
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: "center", padding: 20, backgroundColor: "#f7f7f7" },
    header: { fontSize: 22, fontWeight: "bold", marginBottom: 20, textAlign: "center" },
    input: { borderWidth: 1, padding: 10, marginVertical: 10, borderRadius: 5 },
    result: { fontSize: 18, fontWeight: "bold", marginTop: 20, textAlign: "center" }
});
