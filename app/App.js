import React, { useState } from 'react';
import 'react-native-get-random-values';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, FlatList, Alert, StatusBar, ActivityIndicator, Modal, Platform } from 'react-native';
import { SafeAreaView, SafeAreaProvider } from 'react-native-safe-area-context'; 
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

  // ... (MANTENHA TODAS AS SUAS FUNÇÕES IGUAIS AQUI: gerarSenhaAleatoria, criptografar, etc...) ...
  // Vou resumir para não ficar gigante, mas você copia suas funções de volta se precisar, 
  // ou apenas mude os IMPORTS e o RETURN lá embaixo.
  
  const gerarSenhaAleatoria = () => { /* ... seu código ... */ 
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+";
    let password = "";
    for (let i = 0; i < 16; i++) { password += chars.charAt(Math.floor(Math.random() * chars.length)); }
    setFormSenha(password);
  };
  const copiarParaClipboard = async (senha) => { /* ... seu código ... */ await Clipboard.setStringAsync(senha); Alert.alert("Sucesso", "Copiado!"); };
  const derivarChave = (senha) => { /* ... seu código ... */ const salt = CryptoJS.enc.Utf8.parse("salt_fixo_por_enquanto"); return CryptoJS.PBKDF2(senha, salt, { keySize: 256 / 32, iterations: ITERATIONS, hasher: CryptoJS.algo.SHA256 }); };
  const descriptografarFernet = (token, key) => { /* ... seu código ... */ try { const t = token.replace(/-/g, '+').replace(/_/g, '/'); const th = CryptoJS.enc.Hex.stringify(CryptoJS.enc.Base64.parse(t)); const iv = CryptoJS.enc.Hex.parse(th.substring(18, 50)); const c = CryptoJS.enc.Hex.parse(th.substring(50, th.length - 64)); const k = CryptoJS.enc.Hex.parse(CryptoJS.enc.Hex.stringify(key).substring(32)); const d = CryptoJS.AES.decrypt({ ciphertext: c }, k, { iv: iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 }); return d.toString(CryptoJS.enc.Utf8); } catch (e) { return null; } };
  const criptografarFernet = (d, k) => { /* ... seu código ... */ const kh = CryptoJS.enc.Hex.stringify(k); const sk = CryptoJS.enc.Hex.parse(kh.substring(0, 32)); const ek = CryptoJS.enc.Hex.parse(kh.substring(32)); const iv = CryptoJS.lib.WordArray.random(16); const t = Math.floor(Date.now() / 1000); const tw = CryptoJS.lib.WordArray.create([0, t]); const enc = CryptoJS.AES.encrypt(d, ek, { iv: iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 }); const v = CryptoJS.enc.Hex.parse('80'); const bp = v.clone().concat(tw).concat(iv).concat(enc.ciphertext); const h = CryptoJS.HmacSHA256(bp, sk); const ft = bp.concat(h); const b64 = CryptoJS.enc.Base64.stringify(ft); return b64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
  const sincronizarNaNuvem = async (nl) => { /* ... seu código ... */ setLoading(true); try { const dj = JSON.stringify(nl); const c = derivarChave(senhaMestra); const b = criptografarFernet(dj, c); await axios.post(`${API_URL}/salvar`, { username: usuario, blob_criptografado: b }); setDados(nl); setModalVisible(false); } catch (e) { Alert.alert("Erro", e.message); } finally { setLoading(false); } };
  const fazerLogin = async () => { /* ... seu código ... */ if (!usuario || !senhaMestra) return Alert.alert("Erro", "Preencha tudo"); setLoading(true); setTimeout(async () => { try { const r = await axios.get(`${API_URL}/obter/${usuario}`); const b = r.data.blob; if (!b) { Alert.alert("Novo", "Nenhum dado."); setDados([]); setTela('lista'); } else { const c = derivarChave(senhaMestra); const j = descriptografarFernet(b, c); if (j) { setDados(JSON.parse(j)); setTela('lista'); } else { Alert.alert("Erro", "Senha incorreta."); } } } catch (e) { Alert.alert("Erro", e.message); } finally { setLoading(false); } }, 100); };
  
  // --- INTERFACE (Funções) ---
  const abrirModalAdicionar = () => { setEditandoIndex(null); setFormServico(''); setFormUsuario(''); setFormSenha(''); setModalVisible(true); };
  const abrirModalEditar = (item, index) => { setEditandoIndex(index); setFormServico(item.servico); setFormUsuario(item.usuario); setFormSenha(item.senha); setModalVisible(true); };
  const salvarFormulario = () => { if (!formServico || !formUsuario || !formSenha) return Alert.alert("Erro", "Preencha tudo"); const novo = { servico: formServico, usuario: formUsuario, senha: formSenha }; const l = [...dados]; if (editandoIndex !== null) l[editandoIndex] = novo; else l.push(novo); sincronizarNaNuvem(l); };
  const excluirItem = (index) => { Alert.alert("Excluir", "Certeza?", [{ text: "Cancelar" }, { text: "Apagar", style: "destructive", onPress: () => { const l = dados.filter((_, i) => i !== index); sincronizarNaNuvem(l); } }]); };

  // 3. AQUI ESTÁ A MUDANÇA PRINCIPAL: ENVOLVER TUDO COM SafeAreaProvider
  
  const renderContent = () => {
    if (tela === 'login') {
      return (
        <SafeAreaView style={styles.loginContainer}>
          <StatusBar barStyle="light-content" backgroundColor="#0f172a" />
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
                  <TextInput style={[styles.input, {flex: 1}]} placeholder="Senha" placeholderTextColor="#64748b" value={formSenha} onChangeText={setFormSenha} />
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
  };

  // Envolvo o retorno final com o Provider
  return (
    <SafeAreaProvider>
      {renderContent()}
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  // Nota: Como estamos usando SafeAreaView nativo, talvez não precise mais do paddingTop manual,
  // mas mal não faz manter se quiser garantir.
  container: { flex: 1, backgroundColor: '#0f172a', paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0 },
  loginContainer: { flex: 1, backgroundColor: '#0f172a', justifyContent: 'center' },
  card: { backgroundColor: '#1e293b', margin: 20, padding: 25, borderRadius: 15 },
  logo: { fontSize: 50, textAlign: 'center', marginBottom: 10 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#f8fafc', marginBottom: 30, textAlign: 'center' },
  input: { backgroundColor: '#334155', color: '#fff', padding: 12, borderRadius: 8, marginBottom: 15, fontSize: 16 },
  btnLogin: { backgroundColor: '#2563eb', padding: 15, borderRadius: 8, alignItems: 'center', width: '100%' }, 
  btnModal: { padding: 15, borderRadius: 8, alignItems: 'center', flex: 1 }, 
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