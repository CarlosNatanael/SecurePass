import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, FlatList, Alert, SafeAreaView, StatusBar } from 'react-native';
import axios from 'axios';
import CryptoJS from 'crypto-js';

// --- CONFIGURAÇÃO ---
const API_URL = "http://192.168.1.244:8000"; 

export default function App() {
  const [tela, setTela] = useState('login');
  const [usuario, setUsuario] = useState('');
  const [senhaMestra, setSenhaMestra] = useState('');
  const [dados, setDados] = useState([]);
  const [loading, setLoading] = useState(false);

  // --- CRIPTOGRAFIA COMPATÍVEL COM PYTHON ---
  const derivarChave = (senha) => {
    const salt = CryptoJS.enc.Utf8.parse("salt_fixo_por_enquanto");
    const key = CryptoJS.PBKDF2(senha, salt, {
      keySize: 256 / 32,
      iterations: 100000,
      hasher: CryptoJS.algo.SHA256
    });
    return key;
  };

  const descriptografarFernet = (tokenUrlSafe, keyWordArray) => {
    try {
      const tokenBase64 = tokenUrlSafe.replace(/-/g, '+').replace(/_/g, '/');
      const tokenHex = CryptoJS.enc.Hex.stringify(CryptoJS.enc.Base64.parse(tokenBase64));

      const ivHex = tokenHex.substring(18, 50);
      const iv = CryptoJS.enc.Hex.parse(ivHex);

      const cipherHex = tokenHex.substring(50, tokenHex.length - 64);
      const cipher = CryptoJS.enc.Hex.parse(cipherHex);

      const keyHex = CryptoJS.enc.Hex.stringify(keyWordArray);
      const encKeyHex = keyHex.substring(32); 
      const encKey = CryptoJS.enc.Hex.parse(encKeyHex);

      const decrypted = CryptoJS.AES.decrypt(
        { ciphertext: cipher },
        encKey,
        { iv: iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 }
      );

      return decrypted.toString(CryptoJS.enc.Utf8);
    } catch (error) {
      console.log("Erro na decriptação:", error);
      return null;
    }
  };

const fazerLogin = async () => {
    if (!usuario || !senhaMestra) return Alert.alert("Erro", "Preencha tudo");
    
    setLoading(true);
    try {
      console.log(`Tentando conectar em: ${API_URL}/obter/${usuario}`);
      const response = await axios.get(`${API_URL}/obter/${usuario}`);
      
      // --- DIAGNÓSTICO ---
      console.log("Resposta do servidor:", response.data);
      const blob = response.data.blob;

      if (!blob) {
        Alert.alert("Conectado!", "O servidor respondeu, mas disse que o usuário '" + usuario + "' não tem senhas salvas lá.");
        setDados([]);
        setTela('lista');
      } else {
        Alert.alert("Conectado!", "Baixei um cofre criptografado! Tentando abrir...");
        
        const chave = derivarChave(senhaMestra);
        const jsonDecifrado = descriptografarFernet(blob, chave);

        if (jsonDecifrado) {
          const listaSenhas = JSON.parse(jsonDecifrado);
          setDados(listaSenhas);
          setTela('lista');
        } else {
          Alert.alert("Erro de Senha", "Conectei e baixei os dados, mas a Senha Mestra não conseguiu abrir o cofre.");
        }
      }
    } catch (error) {
      console.log(error);
      Alert.alert("Erro de Conexão", "O celular não achou o PC. Erro: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  // --- INTERFACE ---
  if (tela === 'login') {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" />
        <View style={styles.card}>
          <Text style={styles.logo}>🔐</Text>
          <Text style={styles.title}>SecurePass Mobile</Text>
          
          <Text style={styles.label}>Usuário</Text>
          <TextInput 
            style={styles.input} 
            value={usuario} 
            onChangeText={setUsuario} 
            autoCapitalize="none"
            placeholder="Digite seu usuário"
            placeholderTextColor="#64748b"
          />
          
          <Text style={styles.label}>Senha Mestra</Text>
          <TextInput 
            style={styles.input} 
            value={senhaMestra} 
            onChangeText={setSenhaMestra} 
            secureTextEntry
            placeholder="Sua senha principal"
            placeholderTextColor="#64748b"
          />

          <TouchableOpacity style={styles.btn} onPress={fazerLogin} disabled={loading}>
            <Text style={styles.btnText}>{loading ? "Conectando..." : "Entrar"}</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />
      <View style={styles.header}>
        <Text style={styles.titleSmall}>Minhas Senhas</Text>
        <TouchableOpacity style={styles.btnSair} onPress={() => setTela('login')}>
          <Text style={styles.btnTextSmall}>Sair</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={dados}
        keyExtractor={(item, index) => index.toString()}
        contentContainerStyle={{ paddingBottom: 20 }}
        renderItem={({item}) => (
          <View style={styles.item}>
            <View style={styles.itemIcon}>
              <Text>🔒</Text>
            </View>
            <View style={{flex: 1}}>
              <Text style={styles.itemTitle}>{item.servico}</Text>
              <Text style={styles.itemUser}>{item.usuario}</Text>
            </View>
            <TouchableOpacity onPress={() => Alert.alert("Senha", item.senha)}>
              <Text style={styles.eyeIcon}>👁️</Text>
            </TouchableOpacity>
          </View>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a' },
  card: { backgroundColor: '#1e293b', margin: 20, padding: 25, borderRadius: 15, justifyContent: 'center' },
  logo: { fontSize: 50, textAlign: 'center', marginBottom: 10 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#f8fafc', marginBottom: 30, textAlign: 'center' },
  titleSmall: { fontSize: 20, fontWeight: 'bold', color: '#f8fafc' },
  label: { color: '#cbd5e1', marginBottom: 8, fontWeight: '600' },
  input: { backgroundColor: '#334155', color: '#fff', padding: 15, borderRadius: 8, marginBottom: 20, fontSize: 16 },
  btn: { backgroundColor: '#2563eb', padding: 15, borderRadius: 8, alignItems: 'center' },
  btnText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 20, backgroundColor: '#1e293b' },
  btnSair: { backgroundColor: '#ef4444', paddingVertical: 8, paddingHorizontal: 15, borderRadius: 6 },
  btnTextSmall: { color: '#fff', fontWeight: 'bold' },
  
  item: { backgroundColor: '#1e293b', marginHorizontal: 20, marginTop: 15, padding: 15, borderRadius: 10, flexDirection: 'row', alignItems: 'center' },
  itemIcon: { width: 40, height: 40, backgroundColor: '#334155', borderRadius: 20, alignItems: 'center', justifyContent: 'center', marginRight: 15 },
  itemTitle: { color: '#f8fafc', fontWeight: 'bold', fontSize: 16 },
  itemUser: { color: '#94a3b8', fontSize: 14 },
  eyeIcon: { fontSize: 20, padding: 5 }
});