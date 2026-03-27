/**
 * sync-themes.js
 * Script para automatizar a atualização do themes.json.
 * Execute com: node sync-themes.js
 */

const fs = require('fs');
const path = require('path');

const THEMES_DIR = path.join(__dirname, 'img');
const JSON_FILE = path.join(__dirname, 'themes.json');

// Pastas que NÃO são temas
const EXCLUDE_FOLDERS = ['node_modules', '.git', '.vscode', '.agents', 'assets'];

function sync() {
    console.log('--- Iniciando sincronização de temas (pasta temas/img) ---');
    
    if (!fs.existsSync(THEMES_DIR)) {
        console.error('Diretório temas não encontrado!');
        return;
    }

    const folders = fs.readdirSync(THEMES_DIR).filter(f => {
        const fullPath = path.join(THEMES_DIR, f);
        return fs.statSync(fullPath).isDirectory() && !EXCLUDE_FOLDERS.includes(f);
    });

    let counter = 0;
    const themes = folders.map((folder) => {
        const folderPath = path.join(THEMES_DIR, folder);
        const allFiles = fs.readdirSync(folderPath);

        const mediaFiles = allFiles.filter(file => {
            return /\.(jpg|jpeg|png|webp|mp4|webm|mov)$/i.test(file);
        }).map(file => `img/${folder}/${file}`);

        // Ignora pastas vazias de mídia
        if (mediaFiles.length === 0) return null;

        // Tenta pegar a primeira imagem, ou capa.jpg se existir
        const imgFiles = mediaFiles.filter(f => /\.(jpg|jpeg|png|webp)$/i.test(f));
        let coverFile = imgFiles.find(f => f.toLowerCase().includes('capa')) || imgFiles[0] || mediaFiles[0];
        
        counter++;
        return {
            id: counter,
            tema: folder,
            imagem: coverFile,
            galeria: mediaFiles, 
            categoria: "Temas",
            tags: [folder.toLowerCase()]
        };
    }).filter(t => t !== null);

    fs.writeFileSync(JSON_FILE, JSON.stringify(themes, null, 2), 'utf-8');
    console.log(`Sucesso! ${themes.length} temas sincronizados no arquivo themes.json.`);
}

sync();
