<script setup lang="ts">
import { InboxOutlined, UserOutlined, FileTextOutlined } from '@ant-design/icons-vue';
import { axios, type UploadResponse } from '@lct/services';
import { Steps, UploadDragger, type UploadChangeParam, Button, Divider, Result } from 'ant-design-vue';
import { ref } from 'vue';

import { router } from '@/app/providers/router';
import { useUsersStore } from '@/app/store';

const { logaut, getRole } = useUsersStore();
const isLoading = ref(false);
const uploadStartTime = ref<null | number>(null);
const current = ref(0);
const result = ref<UploadResponse | null>(null);
const steps = [
  {
    title: 'Инструкция',
    content: 'first-content',
  },
  {
    title: 'Загрузка данных',
    content: 'second-content',
  },
  {
    title: 'Результат',
    content: 'third-content',
  },
];
const items = steps.map((item) => ({ key: item.title, title: item.title }));
const uploadUrl = `${import.meta.env.VITE_BACKEND_URL}flights/flight-plans/upload_excel/`;
const credentials = btoa(`${import.meta.env.VITE_ADMIN_USERNAME}:${import.meta.env.VITE_ADMIN_PASSWORD}`);
const headers = {
  Authorization: `Basic ${credentials}`,
};

const formatDuration = (ms: number): string => {
  const totalSeconds = Math.floor(ms / 1000);

  if (totalSeconds < 60) {
    return `${totalSeconds} сек`;
  }

  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  if (seconds === 0) {
    return `${minutes} мин`;
  }

  return `${minutes} мин ${seconds} сек`;
};
const handleChange = (info: UploadChangeParam) => {
  const file = info.file;

  // Запоминаем время начала загрузки
  if (file.status === 'uploading' && uploadStartTime.value === null) {
    uploadStartTime.value = performance.now();
  }

  if (file.status === 'done') {
    const endTime = performance.now();
    const durationMs = endTime - uploadStartTime.value!;
    uploadStartTime.value = null;

    const formattedTime = formatDuration(durationMs);

    // Добавляем время в response (мутируем — не идеально, но работает)
    if (typeof file.response === 'object' && file.response !== null) {
      file.response.loading_time_minutes = formattedTime;
    } else {
      // Если response — строка или null, создаём объект
      file.response = {
        success: true,
        message: 'Файл успешно обработан',
        loading_time_minutes: formattedTime,
      };
    }

    current.value = 2;
    result.value = file.response;
  } else if (file.status === 'error') {
    uploadStartTime.value = null;
    console.error('Upload failed', file.error);
  }
};
function handleDrop(e: DragEvent) {
  console.log(e);
}

const goToLoadDashboard = () => {
  router.push({ name: 'home' });
};

const nextStep = () => {
  current.value++;
};

const prevStep = () => {
  current.value--;
};

const getExportData = async () => {
  try {
    isLoading.value = true;
    const response = await axios.get('/flights/statistics/export_regional_annual_excel/', {
      responseType: 'blob',
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;

    let fileName = `fly-drone-export-${new Date().toISOString().slice(0, 10)}.xlsx`; // имя по умолчанию

    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();

    window.URL.revokeObjectURL(url);
    link.remove();

    isLoading.value = false;
  } catch (error) {
    isLoading.value = false;
    console.error('Ошибка при скачивании файла:', error);
  }
};
</script>

<template>
  <div class="container mx-auto py-10">
    <div class="mb-10 flex items-center">
      <div class="flex items-center gap-5">
        <div class="flex items-center gap-1">
          <UserOutlined class="size-5" />
          <p v-if="getRole() === 'admin'">Администратор</p>
          <p v-else>Пользователь</p>
        </div>
        <div class="flex items-center gap-3">
          <Button type="primary" v-if="current < 1" @click="nextStep">Перейти к загрузке</Button>
          <Button v-if="current > 0" @click="prevStep">Назад</Button>
        </div>
      </div>
      <div class="ml-auto flex items-center gap-3">
        <Button size="large" type="primary" v-if="getRole() === 'admin'" @click="goToLoadDashboard">Вернуться на дашборд</Button>
        <Button size="large" @click="logaut">Выйти</Button>
      </div>
    </div>
    <Steps :current="current" :items="items" />
    <Divider />
    <div v-if="current === 0" class="p-5">
      <div class="upload-container">
        <div class="help-section">
          <h3>📋 Инструкция по загрузке данных</h3>

          <div class="info-block">
            <h4>🔧 Поддерживаемые форматы:</h4>
            <ul>
              <li>Excel файлы (.xlsx, .xls)</li>
              <li>Максимальный размер: 50MB</li>
              <li>Кодировка: UTF-8</li>
            </ul>
          </div>

          <div class="info-block">
            <h4>📊 Структура файла:</h4>
            <p>Excel файл должен содержать следующие столбцы:</p>
            <table class="structure-table">
              <thead>
                <tr>
                  <th>Столбец</th>
                  <th>Описание</th>
                  <th>Пример данных</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>SHR</strong></td>
                  <td>Данные плана полета</td>
                  <td>SHR-ZZZZZ -ZZZZ0700 -M0020/M0030...</td>
                </tr>
                <tr>
                  <td><strong>DEP</strong></td>
                  <td>Данные фактического вылета</td>
                  <td>-TITLE IDEP -SID 7772288076...</td>
                </tr>
                <tr>
                  <td><strong>ARR</strong></td>
                  <td>Данные фактического прибытия</td>
                  <td>-TITLE IARR -SID 7772288076...</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="warning-block">
            <h4>⚠️ Важные моменты:</h4>
            <ul>
              <li>Загрузка нового файла создаст новые планы полетов</li>
              <li>Дубликаты по sid будут пропущены</li>
              <li>Некорректные строки будут проигнорированы с выводом ошибок</li>
              <li>Геопривязка к регионам выполняется автоматически</li>
              <li>Операторы и типы БАС создаются автоматически</li>
            </ul>
          </div>

          <div class="example-block">
            <h4>📝 Пример реальных данных в столбце SHR:</h4>
            <pre><code>(SHR-00725
-ZZZZ0600
-M0000/M0005 /ZONA R0,5 4408N04308E/
-ZZZZ0700
-DEP/4408N04308E DEST/4408N04308E DOF/250124
OPR/ГУ МЧС РОССИИ ПО СТАВРОПОЛЬСКОМУ КРАЮ
REG/00724,REG00725 STS/SAR TYP/BLA
RMK/WR655 В ЗОНЕ ВИЗУАЛЬНОГО ПОЛЕТА
АДМИНИСТРАЦИЯ МУНИЦИПАЛЬНОГО ОКРУГА
ОПЕРАТОР ИВАНОВ +79281234567
SID/7772251137)</code></pre>

            <h5>🔍 Что извлекается из этих данных:</h5>
            <ul>
              <li><strong>ID полета:</strong> 00725</li>
              <li><strong>Время вылета:</strong> 06:00 UTC</li>
              <li><strong>Время посадки:</strong> 07:00 UTC (продолжительность: 1 час)</li>
              <li><strong>Высота полета:</strong> 0-5 метров</li>
              <li><strong>Координаты:</strong> 44.133°N, 43.133°E</li>
              <li><strong>Дата:</strong> 24.01.2025</li>
              <li><strong>Оператор:</strong> ГУ МЧС РОССИИ ПО СТАВРОПОЛЬСКОМУ КРАЮ</li>
              <li><strong>Тип БАС:</strong> BLA (беспилотная авиационная система)</li>
              <li><strong>Цель:</strong> Мониторинг в визуальной зоне полета</li>
            </ul>
          </div>

          <div class="example-block">
            <h4>📝 Пример данных в столбце DEP (фактический вылет):</h4>
            <pre><code>-TITLE IDEP
-SID 7772251137
-ADD 250124
-ATD 0600
-ADEP ZZZZ
-ADEPZ 440846N0430829E
-PAP 0</code></pre>

            <h5>🔍 Что извлекается:</h5>
            <ul>
              <li><strong>Дата вылета:</strong> 24.01.2025</li>
              <li><strong>Время вылета:</strong> 06:00 UTC</li>
              <li><strong>Координаты:</strong> 44.146111°N, 43.141389°E (с точностью до секунд)</li>
            </ul>
          </div>

          <div class="example-block">
            <h4>📝 Пример данных в столбце ARR (фактическое прибытие):</h4>
            <pre><code>-TITLE IARR
-SID 7772251137
-ADA 250124
-ATA 1250
-ADARR ZZZZ
-ADARRZ 440846N0430829E
-PAP 0</code></pre>

            <h5>🔍 Что извлекается:</h5>
            <ul>
              <li><strong>Дата прибытия:</strong> 24.01.2025</li>
              <li><strong>Время прибытия:</strong> 12:50 UTC</li>
              <li><strong>Координаты:</strong> 44.146111°N, 43.141389°E</li>
              <li><strong>Фактическая продолжительность:</strong> 6 часов 50 минут</li>
            </ul>
          </div>
        </div>

        <div class="processing-info">
          <h4>🔄 Что происходит при обработке:</h4>
          <ol>
            <li>Валидация формата и размера файла</li>
            <li>Парсинг структуры Excel файла</li>
            <li>Извлечение данных из столбцов SHR, DEP, ARR</li>
            <li>Создание/поиск операторов БАС</li>
            <li>Создание/поиск типов БАС</li>
            <li>Парсинг координат и временных данных</li>
            <li>Геопривязка к регионам РФ</li>
            <li>Создание планов полетов и фактических данных</li>
            <li>Формирование отчета об обработке</li>
          </ol>
        </div>
      </div>
    </div>
    <div v-if="current === 1" class="p-5">
      <UploadDragger
        accept=".xlsx,.xls"
        :multiple="false"
        name="excel_file"
        :headers="headers"
        :action="uploadUrl"
        @change="handleChange"
        @drop="handleDrop"
      >
        <p class="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p class="ant-upload-text">Нажмите или перетащите файл в эту область для загрузки</p>
        <p class="ant-upload-hint">Поддерживается только одиночная загрузка файлов в формат Excel (xlsx, xls)</p>
      </UploadDragger>
    </div>
    <div v-if="current === 2" class="flex flex-col gap-5 p-5">
      <Result
        :status="result?.success ? 'success' : 'error'"
        :title="result?.message || 'Файл обработан успешно'"
        :sub-title="`Время обработки: ${result?.loading_time_minutes}`"
      >
      </Result>
      <div class="flex flex-col gap-5">
        <div v-if="result?.success" class="flex flex-col rounded-lg border border-slate-200 bg-slate-100 p-3 text-lg">
          <p>Всего обработано планов полетов: {{ result?.total_flight_plans }}</p>
          <p>Не прошли валидацию: {{ result?.validation_failures }}</p>
          <p>Из них успешно загружены: {{ result?.successfully_loaded }}</p>
        </div>

        <Button type="primary" :style="{ boxShadow: '0 6px 16px 0 rgba(1,134,244,0.3)' }" :loading="isLoading" @click="getExportData">
          Выгрузить отчет со статистикой включая все регионы
          <template #icon>
            <FileTextOutlined :style="{ verticalAlign: 'middle', fontSize: '16px' }" />
          </template>
        </Button>
      </div>
    </div>
  </div>
</template>

<style lang="scss">
.ant-steps-item-icon {
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
}

.upload-container {
  max-width: 1000px;
  padding: 20px;
  margin: 0 auto;
}

.help-section {
  padding: 20px;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  margin-bottom: 30px;
  background: #f8f9fa;
}

.info-block {
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
  background: white;
  box-shadow: 0 2px 4px rgb(0 0 0 / 10%);
}

.warning-block {
  padding: 15px;
  border: 1px solid #ffeaa7;
  border-radius: 6px;
  margin-bottom: 20px;
  background: #fff3cd;
}

.example-block {
  padding: 15px;
  border: 1px solid #c3e6c3;
  border-radius: 6px;
  margin-bottom: 20px;
  background: #e8f5e8;
}

.example-block pre {
  padding: 10px;
  border-radius: 4px;
  background: #f8f9fa;
  font-size: 12px;
  line-height: 1.4;
  overflow-x: auto;
}

.structure-table {
  width: 100%;
  margin: 10px 0;
  border-collapse: collapse;
}

.structure-table th,
.structure-table td {
  padding: 8px 12px;
  border: 1px solid #ddd;
  text-align: left;
}

.structure-table th {
  background: #f0f0f0;
  font-weight: bold;
}

.upload-form {
  padding: 30px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 30px;
  background: white;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #333;
  font-weight: bold;
}

.form-group input[type='file'] {
  width: 100%;
  padding: 10px;
  border: 2px dashed #ddd;
  border-radius: 6px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.3s ease;
}

.form-group input[type='file']:hover {
  border-color: #007cba;
  background: #f0f8ff;
}

.help-text {
  margin-top: 5px;
  color: #666;
  font-size: 12px;
  line-height: 1.4;
}

.error-messages {
  margin-top: 10px;
}

.error {
  padding: 8px 12px;
  border-radius: 4px;
  border-left: 3px solid #dc3545;
  margin-bottom: 5px;
  background: #f8d7da;
  color: #721c24;
}

.submit-row {
  display: flex;
  align-items: center;
  margin-top: 25px;
  gap: 15px;
}

.submit-row input[type='submit'] {
  padding: 12px 25px;
  border: none;
  border-radius: 6px;
  background: linear-gradient(135deg, #28a745, #20c997);
  box-shadow: 0 2px 4px rgb(0 0 0 / 10%);
  color: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.submit-row input[type='submit']:hover {
  background: linear-gradient(135deg, #218838, #1ea58a);
  box-shadow: 0 4px 8px rgb(0 0 0 / 20%);
  transform: translateY(-1px);
}

.cancel-link {
  padding: 12px 25px;
  border-radius: 6px;
  background: linear-gradient(135deg, #6c757d, #5a6268);
  box-shadow: 0 2px 4px rgb(0 0 0 / 10%);
  color: white;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.3s ease;
}

.cancel-link:hover {
  background: linear-gradient(135deg, #5a6268, #495057);
  box-shadow: 0 4px 8px rgb(0 0 0 / 20%);
  color: white;
  text-decoration: none;
  transform: translateY(-1px);
}

.processing-info {
  padding: 20px;
  border: 1px solid #bbdefb;
  border-radius: 8px;
  background: #e3f2fd;
}

.processing-info ol {
  padding-left: 20px;
  margin: 10px 0;
}

.processing-info li {
  margin: 8px 0;
  line-height: 1.4;
}

.upload-container h1 {
  padding-bottom: 10px;
  border-bottom: 2px solid #007cba;
  margin-bottom: 30px;
  color: #333;
}

.upload-container h3 {
  margin-top: 0;
  color: #007cba;
}

.upload-container h4 {
  margin: 15px 0 10px;
  color: #495057;
}

/* Responsive design */
@media (width <= 768px) {
  .upload-container {
    padding: 10px;
  }

  .submit-row {
    flex-direction: column;
    align-items: stretch;
  }

  .submit-row input[type='submit'],
  .cancel-link {
    width: 100%;
    text-align: center;
  }

  .structure-table {
    font-size: 12px;
  }

  .structure-table th,
  .structure-table td {
    padding: 6px;
  }
}
</style>
