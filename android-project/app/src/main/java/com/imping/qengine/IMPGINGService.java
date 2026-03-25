package com.imping.qengine;

import android.app.*;
import android.content.*;
import android.os.*;
import android.util.Log;

public class IMPGINGService extends Service {
    private static final String TAG = "IMPGING";
    private Handler threadHandler;
    private boolean running = false;

    @Override
    public void onCreate() {
        super.onCreate();
        Log.i(TAG, "IMPGING Service created");
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        running = true;
        String action = intent != null ? intent.getAction() : "START";

        if ("STOP".equals(action)) {
            stopSelf();
            return START_NOT_STICKY;
        }

        Notification notif = new Notification.Builder(this, "imping_channel")
            .setContentTitle("\u26A1 IMPGING Q-Engine")
            .setContentText("Mimic Engine active | Stealth mode")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setPriority(Notification.PRIORITY_LOW)
            .setOngoing(true)
            .build();

        startForeground(1, notif);

        Log.i(TAG, "IMPGING Service started: " + action);

        return START_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onDestroy() {
        running = false;
        Log.i(TAG, "IMPGING Service destroyed");
        super.onDestroy();
    }
}
