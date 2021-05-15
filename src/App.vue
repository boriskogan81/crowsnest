<template>
    <v-app>
        <v-app-bar
                app
                color="primary"
                dark
        >
            <v-toolbar-title>Crow's Nest</v-toolbar-title>

        </v-app-bar>
        <v-main>
            <v-alert
                    dense
                    text
                    type="success"
                    v-model="alert"
                    dismissible
            >
                Successfully set source/model
            </v-alert>
            <v-row class="d-flex align-content-center justify-space-between mt-4">
                <v-col
                        cols="6"
                        sm="4"
                        class="ml-6"
                >
                    <RedisCard />
                </v-col>
                <v-col
                        cols="6"
                        sm="4"
                        class="mr-6"
                >
                    <v-card
                            class="pa-4"
                            outlined
                            tile
                    >
                        <v-form>
                            <v-select
                                    :items="files"
                                    label="Video files"
                                    outlined
                                    v-on:change="selectFile"
                            ></v-select>
                            <v-select
                                    :items="models"
                                    label="Tensorflow models"
                                    outlined
                                    v-on:change="selectModel"
                            ></v-select>
                            <v-row
                                    class="ml-auto"
                            >
                                <v-btn
                                        color="primary"
                                        v-on:click="sendRequest"
                                >
                                    Send
                                </v-btn>
                            </v-row>
                        </v-form>
                    </v-card>
                </v-col>
            </v-row>

            <v-row
                    class="d-flex justify-center pt-5"
            >
                <v-card
                        class="pa-4"
                        outlined
                        tile
                >
                    <v-img
                            style="max-height: 40vmax; max-width: 50vmax;"
                            src="http://localhost:5000/video"
                    />
                </v-card>
            </v-row>
        </v-main>
    </v-app>
</template>

<script>
    import RedisCard from "@/components/RedisCard";
    export default {
        name: 'App',
        components: {RedisCard},
        data: () => ({
            files: [],
            models: [],
            selectedFile: null,
            selectedModel: null,
            alert: false
        }),
        methods : {
            async sendRequest () {
                try{
                    const response = await fetch('http://localhost:5000/settings',
                        {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded'
                            },
                            body: JSON.stringify({
                                source: this.selectedFile,
                                model: this.selectedModel
                            })
                        })
                    const alertText = await response.json();
                    console.log(alertText)
                    this.alert = alertText.success;
                }
                catch (e) {
                    console.log('failed to send request ', e)
                }
            },
            selectFile(file){
                this.selectedFile = file
            },
            selectModel(model){
                this.selectedModel = model
            }
        },
        async mounted () {
            try{
                const response = await fetch('http://localhost:5000/videos');
                if (!response.ok) {
                    const message = `An error has occured: ${response.status}`;
                    throw new Error(message);
                }
                const files = await response.json();
                this.files = files.map(x => x.replace('\\', '/'))
                const modelResponse = await fetch('http://localhost:5000/models')
                if (!modelResponse.ok) {
                    const message = `An error has occured: ${response.status}`;
                    throw new Error(message);
                }
                const models = await modelResponse.json();
                console.log(models)
                this.models = models.map(x => x.replace('\\', '/'));
            }
            catch (e) {
                console.log(e)
            }

        }
    };
</script>

<style>

    .frame {
        width: 100%;
        height: 100%;
        border: 0;
        transform: scale(2);
        transform-origin: 0 0;
    }


</style>