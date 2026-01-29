import React, { useState } from 'react';
import 'react-native-get-random-values'; 
import { StyleSheet, Text, View, TextInput, TouchableOpacity, FlatList, Alert, SafeAreaView, StatusBar, ActivityIndicator, Modal, Platform } from 'react-native';
import axios from 'axios';
import CryptoJS from 'crypto-js';
import * as Clipboard from 'expo-clipboard';
import { API_URL } from './config';

// --- CONFIGURAÇÃO ---
const ITERATIONS = 5000; 

export default function App() {
  const [tela, setTela] = useState('login'); 
  const [usuario, setUsuario] = useState('');
  const [senhaMestra, setSenhaMestra] = useState('');
  const [dados, setDados] = useState([]);
  const [loading, setLoading] = useState(false);

  // Estados do Modal
  const [modalVisible, setModalVisible] = useState(false);
  const [editandoIndex, setEditandoIndex] = useState(null); 
  const [formServico, setFormServico] = useState('');
  const [formUsuario, setFormUsuario] = useState('');
  const [formSenha, setFormSenha] = useState('');

  // --- FUNÇÕES ÚTEIS ---
  const gerarSenhaAleatoria = () => {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+";
    let password = "";
    for (let i = 0; i < 16; i++) {
      password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setFormSenha(password);
  };

  const copiarParaClipboard = async (senha) => {
    await Clipboard.setStringAsync(senha);
    Alert.alert("Sucesso", "Senha copiada para a área de transferência!");
  };

  // --- CRIPTOGRAFIA ---
  const derivarChave = (senha) => {
    const salt = CryptoJS.enc.Utf8.parse("salt_fixo_por_enquanto");
    return CryptoJS.PBKDF2(senha, salt, {
      keySize: 256 / 32,
      iterations: ITERATIONS,
      hasher: CryptoJS.algo.SHA256
    });
  };

  const descriptografarFernet = (tokenUrlSafe, keyWordArray) => {
    try {
      const tokenBase64 = tokenUrlSafe.replace(/-/g, '+').replace(/_/g, '/');
      const tokenHex = CryptoJS.enc.Hex.stringify(CryptoJS.enc.Base64.parse(tokenBase64));
      const iv = CryptoJS.enc.Hex.parse(tokenHex.substring(18, 50));
      const cipher = CryptoJS.enc.Hex.parse(tokenHex.substring(50, tokenHex.length - 64));
      const encKey = CryptoJS.enc.Hex.parse(CryptoJS.enc.Hex.stringify(keyWordArray).substring(32));

      const decrypted = CryptoJS.AES.decrypt(
        { ciphertext: cipher },
        encKey,
        { iv: iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 }
      );
      return decrypted.toString(CryptoJS.enc.Utf8);
    } catch (error) { return null; }
  };

  const criptografarFernet = (dadosJson, keyWordArray) => {
    const keyHex = CryptoJS.enc.Hex.stringify(keyWordArray);
    const signingKey = CryptoJS.enc.Hex.parse(keyHex.substring(0, 32));
    const encryptionKey = CryptoJS.enc.Hex.parse(keyHex.substring(32));

    const iv = CryptoJS.lib.WordArray.random(16);
    const time = Math.floor(Date.now() / 1000);
    const timeWordArray = CryptoJS.lib.WordArray.create([0, time]); 
    
    const encrypted = CryptoJS.AES.encrypt(dadosJson, encryptionKey, {
      iv: iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7
    });

    const version = CryptoJS.enc.Hex.parse('80');
    const basicParts = version.clone().concat(timeWordArray).concat(iv).concat(encrypted.ciphertext);
    const hmac = CryptoJS.HmacSHA256(basicParts, signingKey);
    const fullToken = basicParts.concat(hmac);
    const base64 = CryptoJS.enc.Base64.stringify(fullToken);
    return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }

  // --- COMUNICAÇÃO ---
  const sincronizarNaNuvem = async (novaLista) => {
    setLoading(true);
    try {
      const dadosJson = JSON.stringify(novaLista);
      const chave = derivarChave(senhaMestra);
      const blob = criptografarFernet(dadosJson, chave);

      await axios.post(`${API_URL}/salvar`, {
        username: usuario,
        blob_criptografado: blob
      });
      
      setDados(novaLista); 
      setModalVisible(false);
    } catch (error) {
      Alert.alert("Erro ao Salvar", "Não foi possível sincronizar: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  const fazerLogin = async () => {
    if (!usuario || !senhaMestra) return Alert.alert("Erro", "Preencha tudo");
    setLoading(true);
    setTimeout(async () => {
      try {
        const response = await axios.get(`${API_URL}/obter/${usuario}`);
        const blob = response.data.blob;

        if (!blob) {
          Alert.alert("Novo Usuário", "Nenhum dado encontrado. Adicione senhas pelo botão +.");
          setDados([]);
          setTela('lista');
        } else {
          const chave = derivarChave(senhaMestra);
          const jsonDecifrado = descriptografarFernet(blob, chave);
          if (jsonDecifrado) {
            setDados(JSON.parse(jsonDecifrado));
            setTela('lista');
          } else {
            Alert.alert("Erro", "Senha Mestra incorreta.");
          }
        }
      } catch (error) { Alert.alert("Erro Conexão", error.message); } 
      finally { setLoading(false); }
    }, 100);
  };

  // --- INTERFACE ---
  const abrirModalAdicionar = () => {
    setEditandoIndex(null);
    setFormServico(''); setFormUsuario(''); setFormSenha('');
    setModalVisible(true);
  };

  const abrirModalEditar = (item, index) => {
    setEditandoIndex(index);
    setFormServico(item.servico); setFormUsuario(item.usuario); setFormSenha(item.senha);
    setModalVisible(true);
  };

  const salvarFormulario = () => {
    if (!formServico || !formUsuario || !formSenha) return Alert.alert("Erro", "Preencha todos os campos");
    const novoItem = { servico: formServico, usuario: formUsuario, senha: formSenha };
    const listaAtualizada = [...dados];
    if (editandoIndex !== null) listaAtualizada[editandoIndex] = novoItem;
    else listaAtualizada.push(novoItem);
    sincronizarNaNuvem(listaAtualizada);
  };

  const excluirItem = (index) => {
    Alert.alert("Excluir", "Tem certeza?", [
      { text: "Cancelar", style: "cancel" },
      { text: "Apagar", style: "destructive", onPress: () => {
          const listaAtualizada = dados.filter((_, i) => i !== index);
          sincronizarNaNuvem(listaAtualizada);
        }}
    ]);
  };

  if (tela === 'login') {
    return (
      <SafeAreaView style={styles.loginContainer}>
        <StatusBar barStyle="light-content" />
        <View style={styles.card}>
          <Text style={styles.logo}>🔐</Text>
          <Text style={styles.title}>SecurePass Mobile</Text>
          <TextInput style={styles.input} value={usuario} onChangeText={setUsuario} autoCapitalize="none" placeholder="Usuário" placeholderTextColor="#64748b" />
          <TextInput style={styles.input} value={senhaMestra} onChangeText={setSenhaMestra} secureTextEntry placeholder="Senha Mestra" placeholderTextColor="#64748b" />
          <TouchableOpacity style={styles.btnLogin} onPress={fazerLogin} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>Acessar Cofre</Text>}
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0f172a" />
      
      <View style={styles.header}>
        <TouchableOpacity style={styles.btnSmall} onPress={() => {setTela('login'); setDados([]);}}>
          <Text style={styles.btnTextSmall}>Sair</Text>
        </TouchableOpacity>
        <Text style={styles.titleSmall}>Minhas Senhas</Text>
        <TouchableOpacity style={styles.btnSmallAdd} onPress={abrirModalAdicionar}>
          <Text style={styles.btnTextAdd}>+</Text>
        </TouchableOpacity>
      </View>

      {dados.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>Cofre vazio.</Text>
          <Text style={styles.emptySubText}>Toque no + para adicionar.</Text>
        </View>
      ) : (
        <FlatList
          data={dados}
          keyExtractor={(item, index) => index.toString()}
          contentContainerStyle={{ paddingTop: 10, paddingBottom: 100 }}
          renderItem={({item, index}) => (
            <View style={styles.item}>
              <View style={styles.itemInfo}>
                <Text style={styles.itemTitle}>{item.servico}</Text>
                <Text style={styles.itemUser}>{item.usuario}</Text>
              </View>
              <View style={styles.actions}>
                <TouchableOpacity onPress={() => copiarParaClipboard(item.senha)} style={styles.actionBtn}>
                  <Text style={styles.actionIcon}>📋</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => abrirModalEditar(item, index)} style={styles.actionBtn}>
                  <Text style={styles.actionIcon}>✏️</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => excluirItem(index)} style={styles.actionBtn}>
                  <Text style={styles.actionIcon}>🗑️</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        />
      )}

      <Modal animationType="slide" transparent={true} visible={modalVisible} onRequestClose={() => setModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>{editandoIndex !== null ? "Editar Senha" : "Nova Senha"}</Text>
            
            <TextInput style={styles.input} placeholder="Serviço" placeholderTextColor="#64748b" value={formServico} onChangeText={setFormServico} />
            <TextInput style={styles.input} placeholder="Usuário" placeholderTextColor="#64748b" value={formUsuario} onChangeText={setFormUsuario} />

            <View style={styles.row}>
                <TextInput 
                    style={[styles.input, {flex: 1}]} 
                    placeholder="Senha" 
                    placeholderTextColor="#64748b" 
                    value={formSenha} 
                    onChangeText={setFormSenha} 
                />
                <TouchableOpacity style={styles.btnGenerate} onPress={gerarSenhaAleatoria}>
                    <Text style={{fontSize: 20}}>🎲</Text>
                </TouchableOpacity>
            </View>

            <View style={styles.modalButtons}>
              <TouchableOpacity style={[styles.btnModal, styles.btnCancel]} onPress={() => setModalVisible(false)}>
                <Text style={styles.btnText}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.btnModal, styles.btnSave]} onPress={salvarFormulario} disabled={loading}>
                {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>Salvar</Text>}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    backgroundColor: '#0f172a',
    // --- LAYOUT ANDROID ---
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0 
  },
  loginContainer: { flex: 1, backgroundColor: '#0f172a', justifyContent: 'center' },
  card: { backgroundColor: '#1e293b', margin: 20, padding: 25, borderRadius: 15 },
  logo: { fontSize: 50, textAlign: 'center', marginBottom: 10 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#f8fafc', marginBottom: 30, textAlign: 'center' },
  input: { backgroundColor: '#334155', color: '#fff', padding: 12, borderRadius: 8, marginBottom: 15, fontSize: 16 },
  
  btnLogin: { backgroundColor: '#2563eb', padding: 15, borderRadius: 8, alignItems: 'center', width: '100%' }, 
  btnModal: { padding: 15, borderRadius: 8, alignItems: 'center', flex: 1 }, 
  
  // Estilo do Botão Gerar Senha
  row: { flexDirection: 'row', gap: 10 },
  btnGenerate: { backgroundColor: '#f59e0b', padding: 12, borderRadius: 8, height: 50, justifyContent: 'center', alignItems: 'center', width: 50 },

  btnText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 15, backgroundColor: '#1e293b' },
  titleSmall: { fontSize: 18, fontWeight: 'bold', color: '#f8fafc' },
  btnSmall: { backgroundColor: '#ef4444', padding: 8, borderRadius: 6 },
  btnTextSmall: { color: '#fff', fontWeight: 'bold' },
  btnSmallAdd: { backgroundColor: '#10b981', padding: 8, borderRadius: 6, width: 40, alignItems: 'center' },
  btnTextAdd: { color: '#fff', fontWeight: 'bold', fontSize: 18, lineHeight: 20 },
  
  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptyText: { color: '#64748b', fontSize: 18 },
  emptySubText: { color: '#475569' },
  item: { backgroundColor: '#1e293b', marginHorizontal: 15, marginBottom: 10, padding: 15, borderRadius: 10, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  itemInfo: { flex: 1 },
  itemTitle: { color: '#f8fafc', fontWeight: 'bold', fontSize: 16 },
  itemUser: { color: '#94a3b8', fontSize: 14 },
  actions: { flexDirection: 'row' },
  actionBtn: { padding: 8, marginLeft: 5 },
  actionIcon: { fontSize: 20 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 20 },
  modalCard: { backgroundColor: '#1e293b', padding: 20, borderRadius: 15 },
  modalTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff', marginBottom: 20, textAlign: 'center' },
  modalButtons: { flexDirection: 'row', gap: 10, marginTop: 10 },
  btnCancel: { backgroundColor: '#64748b' },
  btnSave: { backgroundColor: '#2563eb' },
});