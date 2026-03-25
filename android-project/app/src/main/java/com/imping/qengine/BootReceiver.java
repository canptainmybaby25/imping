package com.imping.qengine;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            Intent svc = new Intent(ctx, IMPGINGService.class);
            svc.setAction("START");
            ctx.startForegroundService(svc);
        }
    }
}
